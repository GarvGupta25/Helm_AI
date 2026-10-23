"""Capability-scoped research API: generated catalogue only, bounded session state."""
import hmac
import json
import os
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from secrets import token_urlsafe

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import session
from ..public_assistant import _check_rate_limit
from .engine import recommend
from .generator import CONFIG, generate, validate
from .intent import extract_intent
from .models import ResearchRecord, ResearchSession
from .schemas import Consent, Conversation, Evidence, Feedback, Profile
from .storage import stable_key

router = APIRouter(prefix="/api/v1", tags=["synthetic research"])


class GenerateRequest(BaseModel):
    seed: int = Field(default=CONFIG["seed"], ge=0, le=2147483647)
    version: str = Field(default=CONFIG["version"], pattern=r"^[A-Za-z0-9_-]{1,60}$")


@router.post("/synthetic/generate")
def generate_exports(body: GenerateRequest, request: Request, authorization: str = Header(default="")):
    admin = os.getenv("SYNTHETIC_ADMIN_TOKEN", "")
    if not admin or not hmac.compare_digest(authorization, "Bearer "+admin):
        raise HTTPException(403, "Developer-only generation is disabled or requires the configured administrator bearer token. CLI generation is available locally.")
    _check_rate_limit("generator:"+(request.client.host if request.client else "unknown"))
    data = generate({**CONFIG, "seed": body.seed, "version": body.version})
    report = validate(data)
    target = Path(__file__).resolve().parents[3]/".runtime"/f"synthetic-{body.version}-{body.seed}"
    target.mkdir(parents=True, exist_ok=True)
    for kind, values in data.items():
        (target/f"{kind}.json").write_text(json.dumps(values), encoding="utf-8")
    (target/"quality.json").write_text(json.dumps(report), encoding="utf-8")
    return {"report": report, "imported": False, "notice": "Generated local exports only. Use the explicit administrator import CLI to activate a catalogue."}


@router.get("/evaluation/summary")
def evaluation_summary():
    path = Path(__file__).resolve().parents[3]/"docs/research/evaluation.json"
    if not path.exists():
        raise HTTPException(503, "Run research_evaluate.py to produce the offline fixture evaluation first.")
    return json.loads(path.read_text(encoding="utf-8"))


def catalogue(db):
    rows = db.scalars(select(ResearchRecord).where(ResearchRecord.kind == "variants")).all()
    if not rows:
        raise HTTPException(503, "Synthetic catalogue not imported. Run the administrator research_data CLI.")
    return [r.data for r in rows]


def own(db: Session = Depends(session), x_research_session: str = Header(default="")):
    record = db.get(ResearchSession, x_research_session) if len(x_research_session) == 43 else None
    if not record:
        raise HTTPException(404, "Research session not found. Start a new session.")
    if record.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        db.delete(record)
        db.commit()
        raise HTTPException(410, "Research session expired and was deleted.")
    return record


def save(db, record, data):
    record.data = deepcopy(data)
    db.commit()


def active_memory(data):
    if not data.get("consent", {}).get("personalization"):
        return []
    now = datetime.now(timezone.utc).isoformat()
    return [m for m in data.get("memory", []) if m["valid_until"] > now and m.get("confirmed")]


def run_engine(db, data, profile=None):
    result = recommend(catalogue(db), profile or Profile(**data["profile"]), active_memory(data))
    result.update(run_id=token_urlsafe(16), profile_version=data["version"])
    before = data.get("runs", [])[-1]["items"] if data.get("runs") else []
    old = {p["id"]: (rank+1, p["fusion"]) for rank, p in enumerate(before)}
    result["deltas"] = [{"id": p["id"], "rank": i+1, "previous_rank": old.get(p["id"], (None, None))[0],
                         "score_delta": round(p["fusion"]-old[p["id"]][1], 4) if p["id"] in old else None}
                        for i, p in enumerate(result["items"])]
    data["runs"] = [*data.get("runs", [])[-4:], result]
    return result


@router.get("/synthetic/catalogue/stats")
def stats(db: Session = Depends(session)):
    plans = catalogue(db)
    return {"source": "synthetic", "variants": len(plans), "insurers": len({p["insurer_id"] for p in plans}), "version": CONFIG["version"]}


@router.get("/plans")
def plans(limit: int = 30, db: Session = Depends(session)):
    return catalogue(db)[:max(1, min(100, limit))]


@router.get("/plans/{plan_id}")
def plan(plan_id: str, db: Session = Depends(session)):
    record = db.get(ResearchRecord, plan_id)
    if not record or record.kind != "variants":
        raise HTTPException(404, "Synthetic plan not found")
    clauses = db.scalars(select(ResearchRecord).where(ResearchRecord.kind == "clauses")).all()
    return {**record.data, "clauses": [c.data for c in clauses if c.data["variant_id"] == plan_id]}


@router.post("/profile/validate")
def validate_profile(body: Profile):
    return body


@router.post("/research/sessions")
def create(body: Profile, request: Request, db: Session = Depends(session)):
    _check_rate_limit("research-create:"+(request.client.host if request.client else "unknown"))
    catalogue(db)
    data = {"profile": body.model_dump(mode="json"), "version": 1, "history": [], "memory": [],
            "consent": Consent().model_dump(), "runs": [], "feedback": []}
    record = ResearchSession(data=data, expires_at=datetime.now(timezone.utc)+timedelta(hours=24))
    db.add(record)
    db.flush()
    result = run_engine(db, data)
    save(db, record, data)
    return {"session_token": record.id, "profile": body, "result": result, "expires_at": record.expires_at}


@router.get("/profile/history")
def history(record=Depends(own)):
    return {"profile": record.data["profile"], "version": record.data["version"], "history": record.data["history"], "memory": active_memory(record.data)}


def apply_profile(db, record, body):
    data = deepcopy(record.data)
    old = data["profile"]
    updated = body.model_dump(mode="json")
    changes = {k: {"before": old.get(k), "after": v} for k, v in updated.items() if k != "evidence" and old.get(k) != v}
    for key in changes:
        updated["evidence"][key] = Evidence(value=updated[key]).model_dump(mode="json")
    data["history"] = [*data["history"][-19:], {"version": data["version"], "profile": old, "diff": changes}]
    data["version"] += 1
    data["profile"] = updated
    result = run_engine(db, data)
    save(db, record, data)
    return {"profile": updated, "diff": changes, "result": result}


@router.patch("/profile")
def update(body: Profile, record=Depends(own), db: Session = Depends(session)):
    return apply_profile(db, record, body)


@router.post("/profile/undo")
def undo(record=Depends(own), db: Session = Depends(session)):
    if not record.data["history"]:
        raise HTTPException(409, "No profile change to undo")
    data = deepcopy(record.data)
    previous = data["history"].pop()
    data["profile"] = previous["profile"]
    data["version"] += 1
    result = run_engine(db, data)
    save(db, record, data)
    return {"profile": data["profile"], "result": result}


@router.post("/profile/extract")
def extraction(body: Conversation, record=Depends(own)):
    return extract_intent(body.message, record.data["profile"], body.external_processing_consent)


@router.post("/conversation/message")
def conversation(body: Conversation, record=Depends(own), db: Session = Depends(session)):
    digest = sha256(body.message.encode()).hexdigest()
    if body.confirm:
        pending = record.data.get("pending", {})
        if pending.get("hash") != digest or pending.get("version") != record.data["version"]:
            raise HTTPException(409, "Review the proposed changes for this profile version first.")
        try:
            profile = Profile(**{**record.data["profile"], **pending["changes"]})
        except ValidationError:
            raise HTTPException(422, "Proposed preference values are outside supported bounds.") from None
        return apply_profile(db, record, profile)
    proposed = extract_intent(body.message, record.data["profile"], body.external_processing_consent)
    data = deepcopy(record.data)
    data["pending"] = {"hash": digest, "version": data["version"], "changes": proposed["proposed"]}
    save(db, record, data)
    return proposed


@router.post("/recommendations")
def recommendations(record=Depends(own), db: Session = Depends(session)):
    data = deepcopy(record.data)
    result = run_engine(db, data)
    save(db, record, data)
    return result


def stored_run(record, run_id):
    result = next((r for r in record.data["runs"] if r["run_id"] == run_id), None)
    if not result:
        raise HTTPException(404, "Run unavailable in this session; only five recent runs retained")
    return result


@router.get("/recommendations/{run_id}")
def get_run(run_id: str, record=Depends(own)):
    return stored_run(record, run_id)


@router.post("/recommendations/{run_id}/what-if")
def what_if(run_id: str, body: Profile, record=Depends(own), db: Session = Depends(session)):
    stored_run(record, run_id)
    data = deepcopy(record.data)
    result = run_engine(db, data, body)
    return {"hypothetical": True, "profile_unchanged": True, "result": result}


@router.get("/recommendations/{run_id}/why/{plan_id}")
@router.get("/recommendations/{run_id}/why-not/{plan_id}")
def why(run_id: str, plan_id: str, record=Depends(own)):
    result = stored_run(record, run_id)
    for item in result["items"]:
        if item["id"] == plan_id:
            return {"status": "selected", "facts": item, "explanation": "Fusion is the weighted sum of the displayed Standard and Contextual scores; annual limits and exclusions remain applicable."}
    for item in result["rejected"]:
        if item["id"] == plan_id:
            return {"status": "filtered", "facts": item}
    return {"status": "not_in_shortlist", "explanation": "Eligible but outside the diverse top three; no coverage failure is implied."}


@router.post("/recommendations/{run_id}/explain-chat")
def explain_chat(run_id: str, body: Conversation, record=Depends(own)):
    result = stored_run(record, run_id)
    return {"reply": "These are the computed comparison facts. Explanations cannot invent policy terms or change rank.",
            "facts": [{"id": p["id"], "S": p["standard"]["score"], "C": p["contextual"]["score"], "F": p["fusion"], "clauses": p["evidence_ids"]} for p in result["items"]]}


@router.post("/feedback")
def feedback(body: Feedback, record=Depends(own), db: Session = Depends(session)):
    shown = {p["id"] for r in record.data["runs"] for p in r["items"]}
    if body.plan_id not in shown:
        raise HTTPException(422, "Feedback must reference an exposed plan in this session")
    data = deepcopy(record.data)
    data["feedback"] = [*data["feedback"][-99:], {**body.model_dump(), "at": datetime.now(timezone.utc).isoformat(), "inferred_preference": False}]
    save(db, record, data)
    return {"recorded": True, "ranking_changed": False, "training": False}


@router.get("/consent")
def consent(record=Depends(own)):
    return record.data["consent"]


@router.patch("/consent")
def set_consent(body: Consent, record=Depends(own), db: Session = Depends(session)):
    if body.durable_memory and not stable_key():
        raise HTTPException(503, "Durable memory needs a stable server encryption key. Session-only comparison remains available.")
    data = deepcopy(record.data)
    data["consent"] = body.model_dump()
    now = datetime.now(timezone.utc)
    record.expires_at = now+timedelta(days=90) if body.durable_memory else now+timedelta(hours=24)
    if body.durable_memory:
        data["memory"] = [{"id": field, "field": field, "value": value, "source": "confirmed_memory",
                           "confirmed": True, "observed_at": now.isoformat(), "valid_until": (now+timedelta(days=90)).isoformat(), "scope": "enduring"}
                          for field, value in data["profile"].items() if field == "preferred" and value]
    else:
        data["memory"] = []
    save(db, record, data)
    return {"consent": body, "expires_at": record.expires_at, "memory": data["memory"]}


@router.get("/memory")
def memory(record=Depends(own)):
    return record.data.get("memory", [])


@router.delete("/memory/{memory_id}")
def forget(memory_id: str, record=Depends(own), db: Session = Depends(session)):
    data = deepcopy(record.data)
    data["memory"] = [m for m in data["memory"] if m["id"] != memory_id]
    save(db, record, data)
    return {"deleted": True}


@router.patch("/memory/{memory_id}")
def edit_memory(memory_id: str, body: Evidence, record=Depends(own), db: Session = Depends(session)):
    if memory_id != "preferred" or not isinstance(body.value, list):
        raise HTTPException(422, "Only confirmed soft benefit preferences may be remembered")
    Profile(preferred=body.value)
    if not record.data["consent"]["durable_memory"]:
        raise HTTPException(409, "Enable durable memory first")
    data = deepcopy(record.data)
    data["memory"] = [{"id": "preferred", "field": "preferred", **body.model_dump(mode="json"),
                       "source": "confirmed_memory", "confirmed": True, "scope": "enduring",
                       "valid_until": (datetime.now(timezone.utc)+timedelta(days=90)).isoformat()}]
    save(db, record, data)
    return data["memory"]


@router.get("/me")
def export(record=Depends(own)):
    return record.data


@router.delete("/me")
def delete_me(record=Depends(own), db: Session = Depends(session)):
    db.delete(record)
    db.commit()
    return {"deleted": True}


@router.get("/model-cards")
def cards():
    return {"version": CONFIG["version"], "source": "synthetic", "learned_ranking": "disabled; no demonstrated incremental value",
            "extractor": "deterministic ontology baseline; external LLM not enabled", "weights": CONFIG,
            "limitations": ["Not real quotes", "No clinical or actuarial validation", "Synthetic service metrics", "No sales"]}
