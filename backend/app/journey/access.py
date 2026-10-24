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

from ..db import session
from ..models import now
from ..public_assistant import _check_rate_limit
from .case_models import Case, Contact, Grant, Job
from .cases import active, audit, case_owned, live_case
from .contact import check_code, keyed, normalize
from .router import digest, owned
from .schemas import Strict

router = APIRouter(prefix="/api/journey", tags=["private demo access"])


def same_origin(request):
    origin = request.headers.get("origin")
    if request.headers.get("sec-fetch-site") == "cross-site" or (origin and urlparse(origin).netloc != request.url.netloc):
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
        destination = normalize(body.channel, body.destination)
        contacts = db.scalars(select(Contact).where(Contact.id.in_(case.data['contact_ids']), Contact.channel == body.channel)).all()
        contact = next((c for c in contacts if c.lookup_hash == keyed(destination) and c.verified_at), None)
        if contact:
            code = f'{randbelow(1000000):06}'
            data = deepcopy(contact.data)
            data.update(challenge_hash=keyed(contact.id+code), expires_at=(now()+timedelta(minutes=10)).isoformat(), attempts=0, consumed=False, recovery_case=case.id)
            contact.data = data
            contact_id = contact.id
            db.add(Job(case_id=case.id, contact_id=contact.id, kind='verification', dedupe_key='recovery:'+token_urlsafe(16), status='delivered_demo', due_at=now(), data={'code': code, 'expires_at': data['expires_at'], 'notice': 'Recovery verification in your private demo mailbox.'}))
            db.commit()
    except HTTPException:
        pass
    return {'contact_id': contact_id, 'notice': 'If the case and verified contact match, a code is available in your protected demo mailbox. Enter it to request a new link.'}


class RecoverVerify(Strict):
    case_id: str
    contact_id: str
    code: str = Field(pattern=r'^\d{6}$')


@router.post('/access-links/recover/verify')
def recover_verify(body: RecoverVerify, request: Request, db: Session = Depends(session)):
    same_origin(request)
    case = live_case(db.get(Case, body.case_id))
    contact = db.scalar(select(Contact).where(Contact.id == body.contact_id).with_for_update())
    if not contact or contact.id not in case.data['contact_ids'] or contact.data.get('recovery_case') != case.id:
        raise HTTPException(422, 'Code could not be verified')
    check_code(db, contact, body.code)
    result = issue_link(db, case)
    db.commit()
    return result
