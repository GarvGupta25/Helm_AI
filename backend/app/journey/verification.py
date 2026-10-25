"""Allow-listed official transports; local demo never sends externally."""
import re
import smtplib
from copy import deepcopy
from datetime import datetime, timedelta
from email.message import EmailMessage
from secrets import randbelow, token_urlsafe
from typing import Literal, Protocol

import httpx
import phonenumbers
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..db import session
from ..models import now
from ..public_assistant import _check_rate_limit
from ..research.storage import stable_key
from .access import same_origin
from .case_models import Contact, Grant, OtpWindow
from .contact import check_code, keyed
from .router import digest, owned, save
from .schemas import Strict
from .selection import selected
from .whatsmcp import WhatsMCPError, WhatsMCPOtpProvider, configured

router=APIRouter(prefix='/api/journey',tags=['verified contact'])
demo_codes: dict[str,tuple[str,datetime]] = {}


class OtpDeliveryProvider(Protocol):
    def send(self, destination: str, code: str, contact_id: str): ...


class ConsoleProvider:
    def send(self, destination, code, contact_id):
        if settings().app_env not in {'development','test'}:
            raise ValueError('Local verification is unavailable outside development/test')
        for ident,(_,expiry) in list(demo_codes.items()):
            if expiry<=now():
                del demo_codes[ident]
        if len(demo_codes)>=1000:
            raise ValueError('Demo inbox is busy')
        demo_codes[contact_id]=(code,now()+timedelta(minutes=10))
        print('Local verification prepared (destination and code hidden).',flush=True)


class WhatsAppCloudProvider:
    def send(self, destination, code, contact_id):
        config=settings()
        if not (config.whatsapp_access_token and config.whatsapp_phone_number_id.isdigit() and re.fullmatch(r'v\d+\.\d+',config.whatsapp_graph_version) and config.whatsapp_auth_template):
            raise ValueError('Configure the official WhatsApp authentication template')
        payload={'messaging_product':'whatsapp','to':destination.lstrip('+'),'type':'template','template':{'name':config.whatsapp_auth_template,'language':{'code':config.whatsapp_template_language},'components':[{'type':'body','parameters':[{'type':'text','text':code}]},{'type':'button','sub_type':'url','index':'0','parameters':[{'type':'text','text':code}]}]}}
        with httpx.Client(timeout=8,follow_redirects=False) as client:
            response=client.post(f'https://graph.facebook.com/{config.whatsapp_graph_version}/{config.whatsapp_phone_number_id}/messages',headers={'Authorization':'Bearer '+config.whatsapp_access_token},json=payload)
            if response.status_code>=300 or not response.json().get('messages'):
                raise ValueError('WhatsApp did not accept the verification message')


class EmailProvider:
    def send(self,destination,code,contact_id):
        config=settings()
        if not (config.smtp_host and config.smtp_from and config.smtp_user and config.smtp_password):
            raise ValueError('Configure the encrypted SMTP fallback')
        message=EmailMessage()
        message['Subject']='Your Helm verification code'
        message['From']=config.smtp_from
        message['To']=destination
        message.set_content(f'Your verification code is {code}. It expires in10 minutes. Do not share it. This is a fictional insurance demonstration.')
        with smtplib.SMTP_SSL(config.smtp_host,config.smtp_port,timeout=8) as client:
            client.login(config.smtp_user,config.smtp_password)
            client.send_message(message)


def destination(channel,country_code,number):
    value=number.strip()
    if channel=='email':
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value) or len(value)>180:
            raise HTTPException(422,'Enter a valid email address')
        return value.casefold()
    if not re.fullmatch(r'\+?\d{1,3}',country_code):
        raise HTTPException(422,'Choose a country calling code')
    try:
        if not value.startswith('+'):
            code=int(country_code.lstrip('+'))
            region=phonenumbers.region_code_for_country_code(code)
            if region=='001' or not region:
                raise ValueError()
            parsed=phonenumbers.parse(value,region)
        else:
            parsed=phonenumbers.parse(value,None)
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError()
        return phonenumbers.format_number(parsed,phonenumbers.PhoneNumberFormat.E164)
    except (ValueError,phonenumbers.NumberParseException):
        raise HTTPException(422,'Enter a valid international phone number for the selected country') from None


def provider(channel,value):
    mode=settings().otp_delivery_mode
    if mode in {'twilio','mock'} and channel=='whatsapp':
        from .twilio_auth import TwilioOtp, mock_enabled, ready
        if mode=='mock' and mock_enabled():
            return ConsoleProvider()
        if mode=='twilio' and ready() and value in settings().otp_allowlist:
            return TwilioOtp()
        raise HTTPException(503,'WhatsApp verification is not configured for this recipient')
    if mode=='console':
        return ConsoleProvider()
    if mode=='whatsmcp' and not configured():
        raise HTTPException(503,'WhatsApp verification is currently unavailable. Please try again later.')
    if value not in settings().otp_allowlist:
        raise HTTPException(422,'Verification is not enabled for this contact. Contact us for help.')
    if mode=='whatsmcp' and channel=='whatsapp':
        return WhatsMCPOtpProvider()
    if mode=='whatsapp_sandbox' and channel=='whatsapp':
        return WhatsAppCloudProvider()
    if mode in {'email_sandbox','whatsapp_sandbox','whatsmcp'} and channel=='email':
        return EmailProvider()
    raise HTTPException(503,'This verification channel is not configured')


class Start(Strict):
    country_code: str = Field(default='+44',max_length=4)
    number: str = Field(min_length=3,max_length=180)
    channel: Literal['whatsapp','email'] = 'whatsapp'
    consent: Literal[True]
    wording_version: Literal['contact-verification-v1'] = 'contact-verification-v1'


def window(db,key):
    row=db.scalar(select(OtpWindow).where(OtpWindow.key==key).with_for_update())
    if row is None:
        row=OtpWindow(key=key,data={'sends':[]},expires_at=now()+timedelta(hours=2))
        db.add(row)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise HTTPException(429,'Another verification request is in progress. Wait60 seconds.') from None
    return row


def reserve_send(db,session_id,channel,value):
    number_key=keyed('otp-number:'+channel+':'+value)
    session_key=keyed('otp-session:'+session_id)
    windows={key:window(db,key) for key in sorted([number_key,session_key])}
    for key,row in windows.items():
        sends=[at for at in row.data.get('sends',[]) if datetime.fromisoformat(at)>now()-timedelta(hours=1)]
        if len(sends)>=3:
            raise HTTPException(429,'Maximum3 codes per hour for this contact or session. Try later.')
        if key==number_key and sends and (now()-datetime.fromisoformat(sends[-1])).total_seconds()<60:
            raise HTTPException(429,'Wait60 seconds before sending another code')
        row.data={**row.data,'sends':[*sends,now().isoformat()]}
        row.expires_at=now()+timedelta(hours=2)
    return windows[number_key]


@router.get('/verify/config')
def configuration():
    config=settings()
    mode=config.otp_delivery_mode
    approved=bool(config.otp_allowlist)
    whatsapp=approved and ((mode=='whatsmcp' and configured()) or (mode=='whatsapp_sandbox' and bool(config.whatsapp_access_token and config.whatsapp_phone_number_id and config.whatsapp_graph_version and config.whatsapp_auth_template)))
    email=approved and mode in {'email_sandbox','whatsapp_sandbox','whatsmcp'} and bool(config.smtp_host and config.smtp_from and config.smtp_user and config.smtp_password)
    from .twilio_auth import mock_enabled, ready
    if mode in {'twilio','mock'}:
        whatsapp=bool(approved and ready()) if mode=='twilio' else mock_enabled()
    return {'mock':mock_enabled(),'automatic_link':mode in {'twilio','mock'},'mode':mode,'real_delivery':bool((whatsapp or email) and mode!='mock'),'channels':{'whatsapp':bool(whatsapp),'email':bool(email)},'notice':'Developer simulation only.' if mock_enabled() else 'WhatsApp verification is available.' if whatsapp else 'WhatsApp verification is currently unavailable. Please try again later.'}


@router.post('/verify/start')
def start(body:Start,request:Request,record=Depends(owned),db:Session=Depends(session)):
    same_origin(request)
    if not stable_key():
        raise HTTPException(503,'Configure stable encrypted storage before contact verification')
    receipt=selected(record)
    _check_rate_limit('wizard-otp:'+(request.client.host if request.client else 'unknown'))
    value=destination(body.channel,body.country_code,body.number)
    transport=provider(body.channel,value)
    number_window=reserve_send(db,record.id,body.channel,value)
    contact=Contact(session_id=record.id,channel=body.channel,lookup_hash=keyed(value),data={})
    db.add(contact)
    db.flush()
    code=f'{randbelow(1000000):06}'
    managed=settings().otp_delivery_mode=='twilio' and settings().twilio_otp_provider=='twilio_verify'
    ttl=600 if managed or settings().otp_delivery_mode not in {'twilio','mock'} else 300
    contact.data={'destination':value,'challenge_hash':'' if managed else keyed(contact.id+code),'otp_provider':'twilio_verify' if managed else 'custom','expires_at':(now()+timedelta(seconds=ttl)).isoformat(),'attempts':0,'sent_at':now().isoformat(),'selection_fingerprint':receipt['fingerprint'],'mode':settings().otp_delivery_mode,'delivery_status':'pending','messaging_opt_in':{'accepted':True,'wording':body.wording_version,'at':now().isoformat()}}
    number_window.data={**number_window.data,'active_contact_id':contact.id}
    db.commit()
    try:
        delivery=transport.send(value,code,contact.id)
    except WhatsMCPError as exc:
        contact.data={**contact.data,'delivery_status':'failed','consumed':True}
        db.commit()
        raise HTTPException(exc.status_code,str(exc)) from None
    except Exception:
        contact.data={**contact.data,'delivery_status':'failed','consumed':True}
        db.commit()
        raise HTTPException(503,'Verification delivery is unavailable. Check the provider setup or use the other channel.') from None
    contact.data={**contact.data,**(delivery if isinstance(delivery,dict) else {}),'delivery_status':delivery.get('provider_status','sent') if isinstance(delivery,dict) else 'sent'}
    data=deepcopy(record.data)
    data['wizard_contact_id']=contact.id
    save(db,record,data)
    return {'contact_id':contact.id,'channel':body.channel,'mode':settings().otp_delivery_mode,'delivery_status':contact.data['delivery_status'],'resend_after':60,'expires_in':ttl,'notice':'Code available in the private local demo inbox; nothing sent externally.' if settings().otp_delivery_mode in {'console','mock'} else 'Code submitted to the configured messaging provider. Check WhatsApp or your selected email channel.'}


def current_contact(db,record):
    receipt=selected(record)
    contact=db.scalar(select(Contact).where(Contact.id==record.data.get('wizard_contact_id'),Contact.session_id==record.id).with_for_update())
    if not contact or contact.data.get('selection_fingerprint')!=receipt['fingerprint']:
        raise HTTPException(404,'Start verification for the current reviewed selection')
    if contact.data.get('mode')!=settings().otp_delivery_mode:
        raise HTTPException(409,'Request a new code using the current verification service.')
    if contact.data.get('mode')=='twilio' and contact.data.get('otp_provider')!=settings().twilio_otp_provider:
        raise HTTPException(409,'The OTP provider changed; request a new code.')
    return contact


@router.post('/verify/resend')
def resend(request:Request,record=Depends(owned),db:Session=Depends(session)):
    contact=current_contact(db,record)
    return start(Start(number=contact.data['destination'],channel=contact.channel,consent=True),request,record,db)


@router.get('/verify/status')
def status(record=Depends(owned),db:Session=Depends(session)):
    contact=current_contact(db,record)
    sent=datetime.fromisoformat(contact.data['sent_at'])
    return {'contact_id':contact.id,'channel':contact.channel,'mode':contact.data['mode'],'verified':bool(contact.verified_at),'attempts_left':max(0,5-contact.data.get('attempts',0)),'resend_after':max(0,60-int((now()-sent).total_seconds())),'expires_at':contact.data['expires_at']}


@router.get('/verify/demo-code')
def demo_code(record=Depends(owned),db:Session=Depends(session)):
    if settings().otp_delivery_mode not in {'console','mock'} or settings().app_env not in {'development','test'}:
        raise HTTPException(404,'Local inbox unavailable')
    contact=current_contact(db,record)
    entry=demo_codes.get(contact.id)
    if not entry or entry[1]<=now() or contact.data.get('consumed'):
        raise HTTPException(410,'This local code expired or was consumed')
    return {'code':entry[0],'notice':'Simulation only; no real contact ownership is proved.'}


class Check(Strict):
    code: str = Field(pattern=r'^\d{6}$')


@router.post('/verify/check')
def verify(body:Check,request:Request,response:Response,record=Depends(owned),db:Session=Depends(session)):
    same_origin(request)
    contact=current_contact(db,record)
    key=keyed('otp-number:'+contact.channel+':'+contact.data['destination'])
    active=db.get(OtpWindow,key)
    if not active or active.data.get('active_contact_id')!=contact.id or contact.data.get('delivery_status') not in {'sent','queued'}:
        raise HTTPException(410,'A newer code replaced this one, or delivery failed')
    if contact.data.get('otp_provider')=='twilio_verify':
        from .twilio_auth import check_managed
        check_managed(db,contact,body.code)
    else:
        check_code(db,contact,body.code)
    demo_codes.pop(contact.id,None)
    token=token_urlsafe(32)
    db.add(Grant(contact_id=contact.id,token_hash=digest(token),kind='demo_mailbox',expires_at=now()+timedelta(days=7),data={'contacts':[contact.id]}))
    data=deepcopy(record.data)
    data['wizard_verified_contact']=contact.id
    save(db,record,data)
    response.set_cookie('helm_demo_mailbox',token,httponly=True,secure=request.url.scheme=='https',samesite='strict',max_age=604800,path='/api/journey')
    result={'verified':True,'real_ownership_verified':contact.data['mode'] not in {'console','mock'},'contact_id':contact.id}
    if contact.data['mode'] in {'twilio','mock'}:
        from .whatsapp_link import issue_verified_link
        result['magic_link']=issue_verified_link(request,record,db)
    return result
