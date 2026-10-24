from copy import deepcopy
from datetime import timedelta, timezone
from secrets import randbelow, token_urlsafe
from typing import Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..db import session
from ..models import now
from ..public_assistant import _check_rate_limit
from .case_models import Case, Contact, Grant, Job, OtpWindow
from .cases import active, audit, case_owned, live_case
from .contact import check_code, keyed, normalize
from .router import digest, owned
from .schemas import Strict

router = APIRouter(prefix="/api/journey", tags=["private demo access"])


def same_origin(request):
    origin = request.headers.get("origin")
    configured = origin in settings().allowed_origins
    parsed = urlparse(origin or '')
    matches = (parsed.scheme, parsed.netloc) == (request.url.scheme, request.url.netloc)
    if request.headers.get("sec-fetch-site") == "cross-site" or (origin and not matches and not configured):
        raise HTTPException(403, "Use this dashboard's own origin")


def valid_grant(db, token, kind):
    grant = db.scalar(select(Grant).where(Grant.token_hash == digest(token), Grant.kind == kind).with_for_update()) if len(token) == 43 else None
    if not grant or grant.revoked or grant.expires_at.replace(tzinfo=timezone.utc) <= now():
        raise HTTPException(410, "This private access expired or was revoked. Reverify your demo contact to request a new link.")
    return grant


def issue_link(db, case, hours=24):
    live_case(case)
    if not (active(case, 'insurer_share') or active(case, 'broker_share')):
        raise HTTPException(403, "Sharing consent was withdrawn")
    contact = db.get(Contact, case.contact_id)
    if not contact or not contact.verified_at:
        raise HTTPException(422, "Verify a contact before requesting access")
    for previous in db.scalars(select(Grant).where(Grant.case_id == case.id)):
        previous.revoked = True
    token = token_urlsafe(32)
    expiry = min(case.expires_at.replace(tzinfo=timezone.utc), now()+timedelta(hours=hours))
    grant = Grant(case_id=case.id, contact_id=contact.id, token_hash=digest(token), kind='magic_link', expires_at=expiry)
    db.add(grant)
    db.flush()
    db.add(Job(case_id=case.id, contact_id=contact.id, kind='access_link', dedupe_key='access:'+grant.id, status='delivered_demo', due_at=now(),
               data={'url': '/quote-dashboard#'+token, 'text': 'Your private synthetic quote dashboard link. Never share this link.', 'expires_at': expiry.isoformat()}))
    for contact_id in case.data['contact_ids']:
        db.add(Job(case_id=case.id, contact_id=contact_id, kind='link_reminder', dedupe_key=f'reminder:{grant.id}:{contact_id}', due_at=expiry-timedelta(hours=2),
                   data={'grant_id': grant.id, 'template': 'link_expiry_v1', 'text': 'Your synthetic dashboard link expires soon. Open your protected demo inbox to review it.'}))
    audit(case, 'demo_access_link_issued', hours=hours)
    return {'sent_to_demo_inbox': True, 'case_reference': case.id, 'expires_at': expiry}


class Link(Strict):
    case_id: str
    hours: Literal[24, 48] = 24


@router.post('/access-links')
def access_link(body: Link, record=Depends(owned), db: Session = Depends(session)):
    _check_rate_limit('journey-link:'+record.id)
    result = issue_link(db, case_owned(db, record, body.case_id), body.hours)
    db.commit()
    return result


class Exchange(Strict):
    token: str = Field(min_length=43, max_length=43)


@router.post('/access-links/exchange')
def exchange(body: Exchange, request: Request, response: Response, db: Session = Depends(session)):
    same_origin(request)
    _check_rate_limit('journey-exchange:'+(request.client.host if request.client else 'unknown'))
    parent = valid_grant(db, body.token, 'magic_link')
    if parent.used:
        raise HTTPException(410, 'This link was already exchanged. Use the open dashboard or request a new link.')
    case = live_case(db.scalar(select(Case).where(Case.id == parent.case_id).with_for_update()))
    token = token_urlsafe(32)
    grant = Grant(case_id=case.id, contact_id=parent.contact_id, parent_id=parent.id, token_hash=digest(token), kind='dashboard_session',
                  expires_at=min(parent.expires_at.replace(tzinfo=timezone.utc), now()+timedelta(hours=2)))
    parent.used = True
    db.add(grant)
    audit(case, 'dashboard_link_exchanged')
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(410, 'This link was already exchanged') from None
    response.set_cookie('helm_dashboard', token, httponly=True, secure=request.url.scheme == 'https', samesite='strict', max_age=7200, path='/api/journey')
    response.headers['Cache-Control'] = 'no-store'
    return {'case_reference': case.id, 'session_expires_at': grant.expires_at, 'notice': 'Private demonstration access; no customer account or policy was created.'}


def dashboard_case(request: Request, db: Session = Depends(session)):
    grant = valid_grant(db, request.cookies.get('helm_dashboard', ''), 'dashboard_session')
    case = live_case(db.scalar(select(Case).where(Case.id == grant.case_id).with_for_update()))
    if not (active(case, 'insurer_share') or active(case, 'broker_share')):
        raise HTTPException(403, 'Sharing consent withdrawn')
    return case


@router.post('/dashboard/logout')
def logout(request: Request, response: Response, db: Session = Depends(session)):
    same_origin(request)
    grant = valid_grant(db, request.cookies.get('helm_dashboard', ''), 'dashboard_session')
    grant.revoked = True
    db.commit()
    response.delete_cookie('helm_dashboard', path='/api/journey')
    return {'signed_out': True}


class Recovery(Strict):
    case_id: str
    channel: Literal['email', 'whatsapp']
    destination: str = Field(max_length=180)


@router.post('/access-links/recover')
def recover(body: Recovery, request: Request, db: Session = Depends(session)):
    same_origin(request)
    _check_rate_limit('journey-recovery:'+(request.client.host if request.client else 'unknown'))
    case = db.get(Case, body.case_id)
    contact_id = token_urlsafe(16)
    try:
        live_case(case)
        contacts = db.scalars(select(Contact).where(Contact.id.in_(case.data['contact_ids']), Contact.channel == body.channel)).all()
        if any(c.data.get('mode') for c in contacts):
            from .verification import destination as normalized
            destination=normalized(body.channel,'+44',body.destination)
        else:
            destination = normalize(body.channel, body.destination)
        contact = next((c for c in contacts if c.lookup_hash == keyed(destination) and c.verified_at), None)
        if contact:
            if contact.data.get('mode'):
                from .verification import provider, reserve_send
                if contact.data['mode']!=settings().otp_delivery_mode:
                    raise HTTPException(503,'The original verification transport is unavailable')
                transport=provider(body.channel,destination)
                quota=reserve_send(db,case.session_id,body.channel,destination)
                quota.data={**quota.data,'active_contact_id':contact.id}
            code = f'{randbelow(1000000):06}'
            data = deepcopy(contact.data)
            data.update(challenge_hash=keyed(contact.id+code), expires_at=(now()+timedelta(minutes=10)).isoformat(), attempts=0, consumed=False, recovery_case=case.id)
            contact.data = data
            contact_id = contact.id
            if contact.data.get('mode'):
                contact.data={**data,'sent_at':now().isoformat(),'delivery_status':'pending'}
                db.commit()
                try:
                    transport.send(destination,code,contact.id)
                except Exception:
                    contact.data={**contact.data,'consumed':True,'delivery_status':'failed'}
                    db.commit()
                    raise HTTPException(503,'Recovery delivery is unavailable') from None
                contact.data={**contact.data,'delivery_status':'sent'}
            else:
                db.add(Job(case_id=case.id, contact_id=contact.id, kind='verification', dedupe_key='recovery:'+token_urlsafe(16), status='delivered_demo', due_at=now(), data={'code': code, 'expires_at': data['expires_at'], 'notice': 'Recovery verification in your private demo mailbox.'}))
            db.commit()
    except HTTPException:
        pass
    return {'contact_id': contact_id, 'notice': 'If the case and verified contact match, a code is available in your protected local inbox or configured channel. Enter it to request a new link.'}


@router.get('/access-links/recovery-demo-code/{contact_id}')
def recovery_demo_code(contact_id: str,request:Request,db:Session=Depends(session)):
    from .verification import demo_codes
    if settings().otp_delivery_mode!='console' or settings().app_env not in {'development','test'}:
        raise HTTPException(404,'Local recovery inbox unavailable')
    mailbox=valid_grant(db,request.cookies.get('helm_demo_mailbox',''),'demo_mailbox')
    contact=db.get(Contact,contact_id)
    if not contact or contact.id not in mailbox.data['contacts'] or not contact.data.get('recovery_case'):
        raise HTTPException(404,'Recovery code unavailable')
    live_case(db.get(Case,contact.data['recovery_case']))
    entry=demo_codes.get(contact.id)
    if not entry or entry[1]<=now() or contact.data.get('consumed'):
        raise HTTPException(410,'Recovery code expired or consumed')
    return {'code':entry[0],'notice':'Local simulation only; real ownership is not proved.'}


class RecoverVerify(Strict):
    case_id: str
    contact_id: str
    code: str = Field(pattern=r'^\d{6}$')
    hours: Literal[24,48] = 24


@router.post('/access-links/recover/verify')
def recover_verify(body: RecoverVerify, request: Request, db: Session = Depends(session)):
    same_origin(request)
    case = live_case(db.get(Case, body.case_id))
    contact = db.scalar(select(Contact).where(Contact.id == body.contact_id).with_for_update())
    if not contact or contact.id not in case.data['contact_ids'] or contact.data.get('recovery_case') != case.id:
        raise HTTPException(422, 'Code could not be verified')
    if contact.data.get('mode'):
        from .verification import demo_codes
        quota=db.get(OtpWindow,keyed('otp-number:'+contact.channel+':'+contact.data['destination']))
        if not quota or quota.data.get('active_contact_id')!=contact.id or contact.data.get('delivery_status')!='sent':
            raise HTTPException(410,'This code was replaced or delivery failed')
    check_code(db, contact, body.code)
    if contact.data.get('mode'):
        demo_codes.pop(contact.id,None)
    result = issue_link(db, case,body.hours)
    db.commit()
    return result
