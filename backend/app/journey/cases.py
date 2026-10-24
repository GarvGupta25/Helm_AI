import os
from copy import deepcopy
from datetime import timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import session
from ..models import now
from .case_models import Case, Contact, QuoteRequest
from .compare import run_owned
from .models import JourneySession
from .router import digest, owned
from .schemas import Strict

router = APIRouter(prefix="/api/journey", tags=["synthetic quote requests"])


def active(case, purpose, recipients=None):
    return any(c["purpose"] == purpose and not c.get("revoked") and (recipients is None or set(recipients) <= set(c["recipients"])) for c in case.data.get("consents", []))


def audit(case, action, actor="visitor", **details):
    data = deepcopy(case.data)
    events = list(data.get("audit", []))
    if len(events) >= 500:
        raise HTTPException(409, "Demo audit capacity reached. Close this case before further actions.")
    events.append({"action": action, "actor": actor, "at": now().isoformat(), "details": details})
    data["audit"] = events
    case.data = data


def live_case(case):
    if not case or case.expires_at.replace(tzinfo=timezone.utc) <= now() or case.data.get("withdrawn"):
        raise HTTPException(410, "This demo case expired or was withdrawn")
    return case


def case_owned(db, record, ident):
    case = db.scalar(select(Case).where(Case.id == ident, Case.session_id == record.id).with_for_update())
    if not case:
        raise HTTPException(404, "Case unavailable")
    return live_case(case)


def source_current(db, case):
    source = db.get(JourneySession, case.session_id)
    if not source or source.version != case.data["profile_version"]:
        raise HTTPException(409, "The confirmed intake changed. Review a new selection before dispatch.")


def requests_for(db, case):
    return [{"id": r.id, "insurer_id": r.insurer_id, "status": r.status, "attempts": r.attempts} for r in db.scalars(select(QuoteRequest).where(QuoteRequest.case_id == case.id))]


def present_case(db, case):
    return {"id": case.id, "state": case.status, "version": case.version, "profile_version": case.data["profile_version"],
            "selected": case.data["selected"], "profile": case.data["profile"], "consents": case.data["consents"],
            "requests": requests_for(db, case), "expires_at": case.expires_at, "broker_assigned": bool(case.broker_id),
            "notice": "Simulation only. No real insurer contacted, no payment collected, and no policy created."}


class RequestQuotes(Strict):
    run_id: str
    expected_version: int
    plan_ids: list[str] = Field(min_length=1, max_length=3)
    contact_ids: list[str] = Field(min_length=1, max_length=2)
    consent_ids: list[str] = Field(min_length=1, max_length=6)
    channels: list[Literal["email", "whatsapp", "dashboard"]] = Field(default_factory=lambda: ["dashboard"], max_length=3)
    quiet_start: int = Field(default=22, ge=0, le=23)
    quiet_end: int = Field(default=8, ge=0, le=23)
    time_zone: str = Field(default="Europe/London", max_length=60)
    demo_acknowledged: Literal[True]


@router.post("/quote-requests")
def request_quotes(body: RequestQuotes, record=Depends(owned), db: Session = Depends(session)):
    run = run_owned(db, record, body.run_id)
    if body.expected_version != record.version or len(set(body.plan_ids)) != len(body.plan_ids):
        raise HTTPException(409, "Review the current distinct selected plans")
    items = [i for i in run.data["result"]["items"] if i["id"] in body.plan_ids]
    if len(items) != len(body.plan_ids):
        raise HTTPException(422, "Choose only plans from your confirmed comparison")
    contacts = [db.scalar(select(Contact).where(Contact.id == ident, Contact.session_id == record.id)) for ident in body.contact_ids]
    if len(set(body.contact_ids)) != len(body.contact_ids) or any(not contact or not contact.verified_at for contact in contacts):
        raise HTTPException(422, "Verify every selected contact in this demo before requesting quotes")
    if len({contact.channel for contact in contacts}) != len(contacts):
        raise HTTPException(422, "Use at most one verified contact for each channel")
    try:
        ZoneInfo(body.time_zone)
    except (ZoneInfoNotFoundError, ValueError):
        raise HTTPException(422, "Choose a valid time zone") from None
    consents = [c for c in record.data.get("sharing_consents", []) if c["id"] in body.consent_ids and not c.get("revoked") and c["profile_version"] == record.version]
    insurers = {i["plan"]["insurer_id"] for i in items}
    if not any(c["purpose"] == "insurer_share" and insurers == set(c["recipients"]) for c in consents):
        raise HTTPException(422, "Explicitly consent to share this version with exactly the selected fictional insurers")
    for channel in set(body.channels)-{"dashboard"}:
        contact = next((c for c in contacts if c.channel == channel), None)
        if not contact or not any(c["purpose"] == "notify_"+channel and contact.id in c["recipients"] for c in consents):
            raise HTTPException(422, "Verify and opt into each chosen notification channel")
    if any(c["purpose"] == "broker_share" and c["recipients"] != ["helm-demo-broker"] for c in consents):
        raise HTTPException(422, "Broker consent must name the Helm demo broker workspace")
    key = digest([record.id, record.version, sorted(body.plan_ids)])
    payload = digest(body.model_dump())
    existing = db.scalar(select(Case).where(Case.request_key == key))
    if existing:
        if existing.data["payload_hash"] != payload:
            raise HTTPException(409, "This selection already has a request. Review the existing case instead of duplicating it.")
        return present_case(db, live_case(existing))
    data = {"profile_version": record.version, "profile": run.data["result"]["profile_snapshot"], "run_id": run.id,
        "selected": items, "consents": consents, "contact_ids": body.contact_ids, "payload_hash": payload,
        "preferences": {"channels": list(set(body.channels)), "quiet_start": body.quiet_start, "quiet_end": body.quiet_end, "time_zone": body.time_zone},
        "flagged_questions": record.data.get("flagged_questions", []), "notes": [], "messages": [], "audit": [], "trigger": "selection_review_confirmed"}
    case = Case(session_id=record.id, contact_id=contacts[0].id, request_key=key, data=data, expires_at=now()+timedelta(days=7))
    if any(c["purpose"] == "broker_share" for c in consents):
        case.broker_id = os.getenv("JOURNEY_DEMO_BROKER_ID") or None
    db.add(case)
    db.flush()
    audit(case, "selection_review_confirmed", selected_count=len(items), insurer_count=len(insurers))
    for insurer in sorted(insurers):
        db.add(QuoteRequest(case_id=case.id, insurer_id=insurer, due_at=now()+timedelta(seconds=3),
            data={"items": [i for i in items if i["plan"]["insurer_id"] == insurer], "adapter": "simulated-insurer-v1", "profile_version": record.version}))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(Case).where(Case.request_key == key))
        if not existing or existing.data["payload_hash"] != payload:
            raise HTTPException(409, "A concurrent selection changed. Reload the request.") from None
        return present_case(db, existing)
    return present_case(db, case)


@router.get("/cases/{case_id}")
def get_case(case_id: str, record=Depends(owned), db: Session = Depends(session)):
    return present_case(db, case_owned(db, record, case_id))


@router.get("/quote-requests/{request_id}")
def get_request(request_id: str, record=Depends(owned), db: Session = Depends(session)):
    row = db.get(QuoteRequest, request_id)
    if not row:
        raise HTTPException(404, "Request unavailable")
    case_owned(db, record, row.case_id)
    return {"id": row.id, "status": row.status, "insurer_id": row.insurer_id}
