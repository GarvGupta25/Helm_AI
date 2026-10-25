"""Compose existing case/request/grant services after reviewed verification."""
from copy import deepcopy
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import session
from ..models import now
from ..public_assistant import _check_rate_limit
from .access import issue_link, same_origin
from .case_models import Contact, Grant, Job, QuoteRequest
from .cases import RequestQuotes, case_owned, request_quotes
from .contact import SharingConsent, consent
from .router import digest, owned, save
from .schemas import Strict
from .selection import selected
from .verification import current_contact

router=APIRouter(prefix='/api/journey',tags=['guided private access'])


def link_delivery(db,grant):
    job=db.scalar(select(Job).where(Job.dedupe_key=='notify-access:'+grant.id))
    return ('accepted' if job.status=='accepted' else job.data.get('provider_status',job.status)) if job else 'not_requested'


@router.get('/wizard/access')
def saved(record=Depends(owned),db:Session=Depends(session)):
    receipt=selected(record)
    metadata=record.data.get('wizard_access')
    if not metadata or metadata.get('fingerprint')!=receipt['fingerprint']:
        raise HTTPException(404,'Choose a link validity first')
    case_owned(db,record,metadata['case_id'])
    grant=db.get(Grant,metadata['grant_id'])
    if not grant or grant.revoked or grant.expires_at.replace(tzinfo=now().tzinfo)<=now():
        raise HTTPException(410,'This link expired or was revoked. Reverify before creating a new link.')
    job=db.scalar(select(Job).where(Job.dedupe_key=='access:'+grant.id))
    return {'case_id':metadata['case_id'],'url':job.data['url'],'expires_at':grant.expires_at,'hours':metadata['hours'],'notifications':metadata['notifications'],'delivery_status':link_delivery(db,grant),'notice':'Private link saved. Never share it. Use your existing dashboard session if this single-use link was already opened.'}


class Access(Strict):
    hours: Literal[24,48]
    notifications: bool = False


@router.post('/wizard/access')
def create(body:Access,request:Request,record=Depends(owned),db:Session=Depends(session)):
    same_origin(request)
    receipt=selected(record)
    contact=current_contact(db,record)
    if not contact.verified_at or record.data.get('wizard_verified_contact')!=contact.id:
        raise HTTPException(422,'Verify your contact for this reviewed selection first')
    metadata=record.data.get('wizard_access',{})
    if metadata and metadata.get('fingerprint')==receipt['fingerprint']:
        case=case_owned(db,record,metadata['case_id'])
        original=db.get(Contact,case.contact_id)
        if original.lookup_hash!=contact.lookup_hash:
            raise HTTPException(403,'Reverify the original contact to renew this private access')
        if metadata['verified_contact_id']==contact.id:
            if metadata['hours']!=body.hours or metadata['notifications']!=body.notifications:
                raise HTTPException(409,'This access choice is already saved. Reverify before changing or renewing it.')
            grant=db.get(Grant,metadata['grant_id'])
            if grant.revoked or grant.expires_at.replace(tzinfo=now().tzinfo)<=now():
                raise HTTPException(410,'Reverify your contact before requesting a new link')
            job=db.scalar(select(Job).where(Job.dedupe_key=='access:'+grant.id))
            return {'case_id':case.id,'url':job.data['url'],'expires_at':grant.expires_at,'reused':True,'delivery_status':link_delivery(db,grant),'notice':'Private access already saved. External delivery requires a configured provider.'}
    else:
        consent_ids=[receipt['insurer_consent_id']]+([receipt['broker_consent_id']] if receipt.get('broker_consent_id') else [])
        channels=['dashboard']
        if body.notifications:
            notification=consent(SharingConsent(purpose='notify_'+contact.channel,recipients=[contact.id],accepted=True,wording_version='journey-sharing-v1'),record,db)
            consent_ids.append(notification['id'])
            channels.append(contact.channel)
        response=request_quotes(RequestQuotes(run_id=receipt['run_id'],expected_version=receipt['profile_version'],plan_ids=receipt['plan_ids'],contact_ids=[contact.id],consent_ids=consent_ids,channels=channels,demo_acknowledged=True),record,db)
        case=case_owned(db,record,response['id'])
        for queued in db.scalars(select(QuoteRequest).where(QuoteRequest.case_id==case.id,QuoteRequest.attempts==0)):
            queued.due_at=now()+timedelta(seconds=3+int(digest(queued.insurer_id)[:2],16)%3)
    _check_rate_limit('journey-link:'+record.id)
    issue_link(db,case,body.hours)
    db.flush()
    grant=db.scalars(select(Grant).where(Grant.case_id==case.id,Grant.kind=='magic_link',Grant.revoked.is_(False)).order_by(Grant.expires_at.desc())).first()
    job=db.scalar(select(Job).where(Job.dedupe_key=='access:'+grant.id))
    # Preserve fragment delivery: a token never enters the HTTP path or server access log.
    job.data={**job.data,'url':job.data['url'].replace('/quote-dashboard#','/my-quotes#')}
    if body.notifications:
        db.add(Job(case_id=case.id,contact_id=case.contact_id,kind='access_link_notify',status='queued',dedupe_key='notify-access:'+grant.id,due_at=now(),data={'template':'private_access_v1','url':job.data['url'],'text':'Your private synthetic quotations are ready to review.'}))
    data=deepcopy(record.data)
    data['wizard_access']={'case_id':case.id,'grant_id':grant.id,'fingerprint':receipt['fingerprint'],'hours':body.hours,'notifications':body.notifications,'verified_contact_id':contact.id}
    save(db,record,data)
    return {'case_id':case.id,'url':job.data['url'],'expires_at':grant.expires_at,'reused':False,'delivery_status':link_delivery(db,grant),'notice':'Your synthetic insurer requests are queued. No real insurer is contacted. Message delivery status is shown separately.'}
