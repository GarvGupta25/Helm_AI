import hashlib
import json
from copy import deepcopy
from datetime import timedelta, timezone
from secrets import token_urlsafe
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..db import session
from ..models import now
from ..public_assistant import _check_rate_limit
from .intake import propose
from .models import JourneySession, ProfileVersion
from .schemas import JourneyProfile, Strict, completeness, sensitive

router = APIRouter(prefix="/api/journey", tags=["synthetic journey"])


def digest(value):
    return hashlib.sha256((value if isinstance(value, str) else json.dumps(value, sort_keys=True)).encode()).hexdigest()


def owned(db: Session = Depends(session), x_journey_session: str = Header(default="")):
    record = db.scalar(select(JourneySession).where(JourneySession.token_hash == digest(x_journey_session)).with_for_update()) if len(x_journey_session) == 43 else None
    if not record:
        raise HTTPException(404, "Journey session unavailable")
    if record.expires_at.replace(tzinfo=timezone.utc) <= now():
        raise HTTPException(410, "Your intake session expired. Start a new session.")
    return record


def save(db, record, data):
    record.data = deepcopy(data)
    flag_modified(record, "data")
    db.commit()


def present(record):
    data = record.data
    profile = JourneyProfile.model_validate(data.get("confirmed", {}))
    return {"profile": profile.model_dump(mode="json"), "draft": data["draft"], "version": record.version,
            "draft_revision": data["draft_revision"], "draft_hash": digest(data["draft"]),
            "latest_run": data.get("latest_run"), "shortlist": data.get("shortlist", {}),
            "health_consent": data.get("health_consent", False), "completeness": completeness(profile), "expires_at": record.expires_at}


@router.post("/sessions")
def create(request: Request, db: Session = Depends(session)):
    _check_rate_limit("journey-create:"+(request.client.host if request.client else "unknown"))
    token = token_urlsafe(32)
    record = JourneySession(token_hash=digest(token), expires_at=now()+timedelta(hours=24),
        data={"draft": JourneyProfile().model_dump(mode="json"), "confirmed": {}, "draft_revision": 0})
    db.add(record)
    db.commit()
    return {"session_token": token, **present(record)}


@router.get("/profile")
def profile(record=Depends(owned)):
    return present(record)


class Draft(Strict):
    expected_revision: int
    profile: JourneyProfile


def check_sensitive(profile, record):
    if sensitive(profile) and not record.data.get("health_consent"):
        raise HTTPException(422, "Agree to the explicit health-preference processing statement before sharing these answers.")
    try:
        completeness(profile)
    except ValueError as error:
        raise HTTPException(422, str(error)) from None


@router.patch("/intake/draft")
def draft(body: Draft, record=Depends(owned), db: Session = Depends(session)):
    if body.expected_revision != record.data["draft_revision"]:
        raise HTTPException(409, "A newer draft exists. Reload before editing.")
    check_sensitive(body.profile, record)
    data = deepcopy(record.data)
    data["draft"] = body.profile.model_dump(mode="json")
    data["draft_revision"] += 1
    save(db, record, data)
    return present(record)


class Proposal(Strict):
    field: str
    message: str
    expected_revision: int
    external_processing_consent: bool = False


@router.post("/intake/proposals")
def proposal(body: Proposal, record=Depends(owned), db: Session = Depends(session)):
    if not 1 <= len(body.message) <= 2000:
        raise HTTPException(422, "Use 1–2000 characters and no identifying or medical details")
    if body.expected_revision != record.data["draft_revision"]:
        raise HTTPException(409, "Review the latest draft first")
    try:
        proposed = propose(body.field, body.message, JourneyProfile.model_validate(record.data["draft"]))
    except ValueError as error:
        raise HTTPException(422, str(error)) from None
    check_sensitive(proposed, record)
    data = deepcopy(record.data)
    data["draft"] = proposed.model_dump(mode="json")
    data["draft_revision"] += 1
    save(db, record, data)
    return {**present(record), "extractor": "deterministic-reviewed-fields", "provider_called": False,
            "notice": "Captured as a draft. Confirm the summary before recommendations."}


class Confirmation(Strict):
    expected_version: int
    draft_hash: str
    source: Literal["manual", "guided_chat"] = "manual"


@router.post("/profile/confirm")
def confirm(body: Confirmation, record=Depends(owned), db: Session = Depends(session)):
    if body.expected_version != record.version or body.draft_hash != digest(record.data["draft"]):
        raise HTTPException(409, "The profile or draft changed. Review it again.")
    current = JourneyProfile.model_validate(record.data["draft"])
    check_sensitive(current, record)
    if record.version >= 50:
        raise HTTPException(409, "This demo keeps up to 50 confirmed versions. Start a new session.")
    data = deepcopy(record.data)
    data["confirmed"] = current.model_dump(mode="json")
    data["latest_run"] = None
    data["shortlist"] = {}
    record.version += 1
    db.add(ProfileVersion(session_id=record.id, version=record.version, data={"profile": data["confirmed"], "source": body.source}))
    save(db, record, data)
    return present(record)


@router.get("/profile/history")
def history(record=Depends(owned), db: Session = Depends(session)):
    return [{"version": row.version, "created_at": row.created_at, "source": row.data["source"]}
            for row in db.scalars(select(ProfileVersion).where(ProfileVersion.session_id == record.id).order_by(ProfileVersion.version.desc()))]


class Version(Strict):
    expected_version: int


@router.post("/profile/undo")
def undo(body: Version, record=Depends(owned), db: Session = Depends(session)):
    if body.expected_version != record.version:
        raise HTTPException(409, "Profile changed. Reload before undo.")
    previous = db.scalar(select(ProfileVersion).where(ProfileVersion.session_id == record.id, ProfileVersion.version < record.version).order_by(ProfileVersion.version.desc()))
    if not previous:
        raise HTTPException(409, "No earlier confirmed version")
    data = deepcopy(record.data)
    data["draft"] = previous.data["profile"]
    data["draft_revision"] += 1
    save(db, record, data)
    return confirm(Confirmation(expected_version=record.version, draft_hash=digest(data["draft"])), record, db)


@router.post("/intake/completeness")
def complete(record=Depends(owned)):
    return present(record)["completeness"]


class HealthPermission(Strict):
    accepted: bool
    wording_version: Literal["health-demo-v1"] = "health-demo-v1"


@router.post("/health-consent")
def health_consent(body: HealthPermission, record=Depends(owned), db: Session = Depends(session)):
    data = deepcopy(record.data)
    data["health_consent"] = body.accepted
    data["health_consent_event"] = {"wording": body.wording_version, "at": now().isoformat(), "accepted": body.accepted}
    if not body.accepted:
        # Withdrawal removes sensitive answers from current and historic intake snapshots.
        for key in ("draft", "confirmed"):
            p = JourneyProfile.model_validate(data.get(key, {})).model_dump(mode="json")
            p["benefits"] = {"required": None, "preferred": []}
            p["health"] = {}
            for person in p["people"]:
                person["smoker_status"] = None
            data[key] = JourneyProfile.model_validate(p).model_dump(mode="json")
        for row in db.scalars(select(ProfileVersion).where(ProfileVersion.session_id == record.id)):
            db.delete(row)
        record.version += 1
        data["draft_revision"] += 1
    save(db, record, data)
    return present(record)
