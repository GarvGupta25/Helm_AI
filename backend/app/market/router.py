"""Capability-protected anonymous demo quotes; no real payment or policy issuance."""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import session
from .models import UKAudit, UKConsent, UKQuote
from .quote import UKQuoteRequest, catalogue, quote

router = APIRouter(prefix="/api/uk", tags=["UK demo"])


@router.get("/plans")
def plans():
    return {"plans": catalogue(), "demo": True}


@router.post("/quotes")
def create_quote(body: UKQuoteRequest, db: Session = Depends(session)):
    snapshot = quote(body)
    identifier = secrets.token_urlsafe(32)
    db.add(UKQuote(id=identifier, snapshot=snapshot, expires_at=datetime.now(timezone.utc) + timedelta(days=7)))
    db.add(UKAudit(intent="quote_created", event={"quote_ref": identifier[:8], "member_count": len(body.members),
               "hospital_list": body.hospital_list, "excess_pence": body.excess_pence}))
    if body.health_consent:
        db.add(UKConsent(quote_id=identifier, purpose="structured-health-data"))
    db.commit()
    return {"quote_id": identifier, **snapshot}


def owned_quote(db, token):
    record = db.get(UKQuote, token)
    if record is None:
        raise HTTPException(404, "Quote not found.")
    expiry = record.expires_at.replace(tzinfo=timezone.utc) if record.expires_at.tzinfo is None else record.expires_at
    if expiry <= datetime.now(timezone.utc):
        raise HTTPException(410, "Quote expired. Please start a new comparison.")
    return record


@router.get("/quotes/current")
def resume_quote(x_quote_token: str = Header(), db: Session = Depends(session)):
    record = owned_quote(db, x_quote_token)
    return {"quote_id": record.id, **record.snapshot, "receipt": record.receipt}


class TestPurchase(BaseModel):
    plan_id: str
    understood_exclusions: Literal[True]
    accepted_status: Literal[True]
    received_ipid: Literal[True]
    test_payment: Literal[True]


@router.post("/quotes/confirm")
def confirm(body: TestPurchase, x_quote_token: str = Header(), db: Session = Depends(session)):
    # Row lock serialises confirmation in Postgres, including retries from two tabs.
    record = db.query(UKQuote).filter(UKQuote.id == x_quote_token).with_for_update().first()
    if record is None:
        raise HTTPException(404, "Quote not found.")
    owned_quote(db, x_quote_token)
    selected = next((plan for plan in record.snapshot["results"] if plan["id"] == body.plan_id), None)
    if selected is None:
        raise HTTPException(422, "Choose a plan from this quote.")
    if record.receipt:
        if record.receipt["plan_id"] != body.plan_id:
            raise HTTPException(409, "This demo quote was already confirmed with a different plan.")
        return record.receipt
    receipt = {"reference": f"DEMO-{secrets.token_hex(6).upper()}", "plan_id": body.plan_id,
               "paid_pence": 0, "status": "simulation_only", "currency": "GBP",
               "premium": selected["premium"], "message": "No money collected. No insurance contract created.",
               "cooling_off": "A real PMI contract generally has a 14-day cancellation period. See the approved terms and refund rules.",
               "documents": [selected["ipid_url"], "/legal/terms-of-business"],
               "demands_and_needs": record.snapshot["demands_and_needs"]}
    record.receipt = receipt
    for purpose in ("exclusions-understood", "status-disclosure", "ipid-received", "test-payment-only"):
        db.add(UKConsent(quote_id=record.id, purpose=purpose))
    db.add(UKAudit(intent="simulation_confirmed", event={"reference": receipt["reference"], "plan_id": body.plan_id}))
    db.commit()
    return receipt


@router.get("/plans/{plan_id}/ipid", response_class=HTMLResponse)
def ipid(plan_id: str):
    plan = next((item for item in catalogue() if item["id"] == plan_id), None)
    if not plan:
        raise HTTPException(404, "Plan not found.")
    return f"""<!doctype html><html lang="en-GB"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{plan['provider']} {plan['tier']} — demo key facts</title>
    <main style="max-width:65ch;margin:50px auto;padding:20px;font:18px/1.7 system-ui">
    <h1>DEMO DATA — illustrative key facts</h1><p>Not an approved Insurance Product Information Document.</p>
    <h2>{plan['provider']} · {plan['tier']}</h2><p>Hospital list: {plan['hospital_list']}.</p>
    <p>Outpatient limit: £{plan['outpatient_limit_pence']/100:,.2f} per policy year.</p>
    <p>Eligible inpatient and day-patient treatment subject to referral, pre-authorisation and underwriting.</p>
    <h2>Usually excluded</h2><p>Chronic and pre-existing conditions, A&amp;E and routine pregnancy care.</p>
    <h2>Your share</h2><p>Selected excess applies per person per policy year. Check all limits before choosing.</p>
    <h2>Cancellation</h2><p>Real contracts generally offer 14 days; check approved policy wording and refund rules.</p>
    <p>No policy is sold by this demo. Version demo-1.</p><a href="/get-cover/quote">Back to comparison</a></main></html>"""
