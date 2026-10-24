from datetime import timedelta, timezone
from typing import Protocol

from fastapi import HTTPException
from sqlalchemy import select

from ..models import now
from .case_models import Case, Document, Job, Quotation, QuoteRequest
from .cases import active, audit, live_case, source_current
from .router import digest


class InsurerAdapter(Protocol):
    def request(self,payload,attempt): ...


class SimulatedInsurerAdapter:
    """No network access: deterministic, frozen prices with explicit failure fixtures."""

    def request(self, payload, attempt):
        fixture = payload.get("simulation", {})
        if attempt <= fixture.get("timeout_attempts", 0):
            raise TimeoutError("Simulated insurer timeout")
        items = payload["items"]
        return items[:1] if fixture.get("partial") else items


def process_quotes(db, clock=None, adapter=None):
    clock = clock or now()
    adapter = adapter or SimulatedInsurerAdapter()
    count = 0
    rows = db.scalars(select(QuoteRequest).where(QuoteRequest.status == "queued", QuoteRequest.due_at <= clock).with_for_update(skip_locked=True)).all()
    for request in rows:
        case = db.scalar(select(Case).where(Case.id == request.case_id).with_for_update())
        try:
            live_case(case)
            source_current(db, case)
            if not active(case, "insurer_share", [request.insurer_id]) or case.status == "closed":
                raise HTTPException(409, "Consent withdrawn or case closed")
        except HTTPException:
            request.status = "cancelled"
            continue
        request.attempts += 1
        try:
            items = adapter.request(request.data, request.attempts)
            expected = {item["id"]: item for item in request.data["items"]}
            if len({item['id'] for item in items}) != len(items) or any(item["id"] not in expected or item != expected[item["id"]] for item in items):
                raise ValueError("Invalid simulated response")
            for item in items:
                document = Document(case_id=case.id, kind="synthetic_quotation", content_hash=digest(item), ai_drafted=False,
                    data={"item": item, "profile_version": case.data["profile_version"], "source": "synthetic", "notice": "No real offer or insurance contract."})
                db.add(document)
                db.flush()
                db.add(Quotation(request_id=request.id, document_id=document.id, plan_id=item["id"], data={"item": item, "source": "synthetic"}, expires_at=min(case.expires_at.replace(tzinfo=timezone.utc), clock+timedelta(hours=48))))
            request.status = "received" if len(items) == len(expected) else "partial"
            audit(case, "synthetic_quotation_received", "demo_worker", request_id=request.id, count=len(items), state=request.status)
            for contact_id in case.data["contact_ids"]:
                db.add(Job(case_id=case.id, contact_id=contact_id, kind="quote_update", due_at=clock,
                    dedupe_key=f"quote-update:{request.id}:{contact_id}", data={"template": "quote_ready_v1", "request_id": request.id, "text": "A synthetic quotation is available in your private demo dashboard."}))
            count += 1
        except TimeoutError:
            request.status = "queued" if request.attempts < 3 else "failed"
            request.due_at = clock+timedelta(seconds=30*request.attempts)
            audit(case, "simulated_insurer_timeout", "demo_worker", request_id=request.id, attempt=request.attempts)
        except ValueError:
            request.status = "failed"
            audit(case, "simulated_insurer_invalid_response", "demo_worker", request_id=request.id)
    db.commit()
    return count
