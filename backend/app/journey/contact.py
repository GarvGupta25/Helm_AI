import hashlib
import hmac
import re
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from secrets import randbelow, token_urlsafe
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import session
from ..models import now
from ..public_assistant import _check_rate_limit
from ..research.storage import _ephemeral_key, stable_key
from .case_models import Case, Contact, Grant, Job
from .router import digest, owned, save
from .schemas import Strict

router = APIRouter(prefix="/api/journey", tags=["demo contact verification"])


def keyed(value):
    key = stable_key().encode() or _ephemeral_key
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()


def normalize(channel, value):
    value = value.strip()
    if channel == "email":
        value = value.casefold()
        if not re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9.-]+\.test", value):
            raise HTTPException(422, "Use a fictional email ending in .test, such as visitor@example.test")
    elif not re.fullmatch(r"\+[1-9]\d{7,14}", value):
        raise HTTPException(422, "Use a fictional international number: + followed by 8–15 digits")
    return value


class Challenge(Strict):
    channel: Literal["email", "whatsapp"]
    destination: str = Field(min_length=3, max_length=180)
    demo_acknowledged: Literal[True]


@router.post("/contacts/challenges")
def challenge(body: Challenge, request: Request, record=Depends(owned), db: Session = Depends(session)):
    _check_rate_limit("journey-otp:"+(request.client.host if request.client else "unknown"))
    destination = normalize(body.channel, body.destination)
    contact = Contact(session_id=record.id, channel=body.channel, lookup_hash=keyed(destination), data={"destination": destination})
    db.add(contact)
    db.flush()
    code = f"{randbelow(1000000):06}"
    data = {"destination": destination, "challenge_hash": keyed(contact.id+code), "expires_at": (now()+timedelta(minutes=10)).isoformat(), "attempts": 0}
    contact.data = data
    db.add(Job(contact_id=contact.id, kind="verification", dedupe_key="verification:"+contact.id,
        status="delivered_demo", due_at=now(), data={"code": code, "notice": "Simulated verification only; no real contact ownership proved.", "expires_at": data["expires_at"]}))
    db.commit()
    return {"contact_id": contact.id, "channel": contact.channel, "delivery": "protected_demo_inbox", "notice": "Nothing was sent externally. Read the code in your private demo inbox."}


def contact_owned(db, record, ident):
    row = db.scalar(select(Contact).where(Contact.id == ident, Contact.session_id == record.id).with_for_update())
    if not row:
        raise HTTPException(404, "Contact unavailable")
    return row


class Verify(Strict):
    contact_id: str
    code: str = Field(pattern=r"^\d{6}$")


def check_code(db, contact, code):
    from datetime import datetime
    data = deepcopy(contact.data)
    if data.get("consumed") or datetime.fromisoformat(data["expires_at"]) <= now():
        raise HTTPException(410, "Verification code expired or already used")
    if data["attempts"] >= 5:
        raise HTTPException(429, "Verification attempt limit reached")
    data["attempts"] += 1
    contact.data = data
    if not hmac.compare_digest(data["challenge_hash"], keyed(contact.id+code)):
        db.commit()
        raise HTTPException(422, "Code could not be verified")
    contact.verified_at = now()
    contact.data = {**data, "consumed": True}
    for job in db.scalars(select(Job).where(Job.contact_id == contact.id, Job.kind == "verification")):
        job.data = {"notice": "Verification consumed", "expires_at": data["expires_at"]}


@router.post("/contacts/verify")
def verify(body: Verify, request: Request, response: Response, record=Depends(owned), db: Session = Depends(session)):
    contact = contact_owned(db, record, body.contact_id)
    if contact.data.get('selection_fingerprint'):
        raise HTTPException(409,'Use the current guided verification flow for this contact')
    check_code(db, contact, body.code)
    token = token_urlsafe(32)
    contacts = db.scalars(select(Contact.id).where(Contact.session_id == record.id, Contact.verified_at.is_not(None))).all()
    db.add(Grant(contact_id=contact.id, token_hash=digest(token), kind='demo_mailbox', expires_at=now()+timedelta(days=7), data={'contacts': list(contacts)}))
    db.commit()
    response.set_cookie('helm_demo_mailbox', token, httponly=True, secure=request.url.scheme == 'https', samesite='strict', max_age=604800, path='/api/journey')
    return {"contact_id": contact.id, "verified_in_demo": True, "real_ownership_verified": False}


@router.get("/demo/inbox")
def inbox(request: Request, db: Session = Depends(session)):
    try:
        record = owned(db, request.headers.get('x-journey-session', ''))
        contacts = db.scalars(select(Contact.id).where(Contact.session_id == record.id)).all()
    except HTTPException:
        if not request.cookies.get('helm_demo_mailbox'):
            raise
        from .access import valid_grant
        grant = valid_grant(db, request.cookies.get('helm_demo_mailbox', ''), 'demo_mailbox')
        contacts = grant.data['contacts']
    jobs = db.scalars(select(Job).where(Job.contact_id.in_(contacts), Job.status == "delivered_demo").order_by(Job.created_at.desc()).limit(30)).all()
    return [{"id": job.id, "kind": job.kind, "contact_id": job.contact_id, "content": job.data} for job in jobs
            if not job.data.get('expires_at') or datetime.fromisoformat(job.data['expires_at']).replace(tzinfo=timezone.utc) > now()]


class SharingConsent(Strict):
    purpose: Literal["insurer_share", "broker_share", "notify_email", "notify_whatsapp"]
    recipients: list[str] = Field(min_length=1, max_length=3)
    accepted: Literal[True]
    wording_version: Literal["journey-sharing-v1"]


@router.post("/consents")
def consent(body: SharingConsent, record=Depends(owned), db: Session = Depends(session)):
    data = deepcopy(record.data)
    events = list(data.get("sharing_consents", []))
    if len(events) >= 30:
        raise HTTPException(409, "Consent history limit reached; start a new demo session")
    event = {"id": token_urlsafe(16), **body.model_dump(), "at": now().isoformat(), "revoked": False, "profile_version": record.version,
             "scope": "Reviewed fictional profile and selected policy snapshots only"}
    events.append(event)
    data["sharing_consents"] = events
    save(db, record, data)
    return event


@router.delete("/consents/{consent_id}")
def withdraw(consent_id: str, record=Depends(owned), db: Session = Depends(session)):
    data = deepcopy(record.data)
    events = deepcopy(data.get("sharing_consents", []))
    event = next((event for event in events if event["id"] == consent_id), None)
    if not event:
        raise HTTPException(404, "Consent unavailable")
    event.update(revoked=True, withdrawn_at=now().isoformat())
    data["sharing_consents"] = events
    for case in db.scalars(select(Case).where(Case.session_id == record.id).with_for_update()):
        snapshot = deepcopy(case.data)
        for c in snapshot.get("consents", []):
            if c["id"] == consent_id:
                c.update(revoked=True, withdrawn_at=now().isoformat())
        case.data = snapshot
        for job in db.scalars(select(Job).where(Job.case_id == case.id, Job.status == "queued")):
            job.status = "cancelled"
        for grant in db.scalars(select(Grant).where(Grant.case_id == case.id)):
            grant.revoked = True
    save(db, record, data)
    return {"withdrawn": True}
