import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy.orm import Session

from ..db import session
from ..public_assistant import _check_rate_limit
from ..research.engine import SCENARIOS, scenario
from .compare import run_owned
from .router import owned, save
from .schemas import Strict

router = APIRouter(prefix="/api/journey", tags=["grounded policy questions"])


def pounds(value):
    return f"£{value / 100:,.2f}"


def answer(item, question):
    """Only release reviewed templates backed by this frozen plan/run."""
    text = question.casefold().strip()
    plan = item["plan"]
    citations = []
    def cite(field, value):
        citations.append({"field": field, "value": value, "plan_id": item["id"], "catalogue_version": plan["version"]})
    unknown = {"kind": "unknown", "reply": "This policy snapshot does not establish that answer. Save this question for a broker; no coverage or cost has been guessed.", "citations": [], "provider_called": False}
    if re.search(r"ignore|system|override|guarantee|implant|waiting|wait period|worldwide|diagnos|medication|passport|jailbreak|<|https?://", text):
        return unknown
    if "scenario" in text or "what would i pay" in text:
        key = next((key for key in SCENARIOS if key in text or key.replace('_', ' ') in text), None)
        if not key:
            return unknown
        calculated = scenario(plan, SCENARIOS[key])
        cite(f"scenario.{key}", calculated)
        cite("quote.annual_pence", item["quote"]["annual_pence"])
        return {"kind": "facts", "reply": f"In the fixed fictional {key.replace('_', ' ')} scenario, member treatment cost is {pounds(calculated['member_pence'])}. Annual premium plus that cost is {pounds(item['quote']['annual_pence']+calculated['member_pence'])}. This uses one adult and the stated synthetic scenario, not a forecast for your household.", "citations": citations, "provider_called": False}
    if any(word in text for word in ("premium", "price", "tax", "monthly", "annual total")):
        for key in ("base_pence", "tax_pence", "monthly_pence", "annual_pence"):
            cite(f"quote.{key}", item["quote"][key])
        reply = f"Monthly base {pounds(item['quote']['base_pence'])}, assumed tax {pounds(item['quote']['tax_pence'])}, total {pounds(item['quote']['monthly_pence'])}. Annual premium {pounds(item['quote']['annual_pence'])}. These are fictional prices, not insurer offers."
    elif "excess" in text:
        cite("plan.excess_pence", plan["excess_pence"])
        cite("plan.excess_application", plan["excess_application"])
        reply = f"The excess is {pounds(plan['excess_pence'])}, applied {plan['excess_application'].replace('_', ' ')} to eligible treatment."
    elif "copay" in text or "co-pay" in text or "co-payment" in text:
        cite("plan.copay", plan["copay"])
        reply = f"The stated copayment is {plan['copay']*100:g}% of eligible treatment after excess, subject to the synthetic limits."
    elif "hospital" in text or "network" in text:
        cite("plan.network", plan["network"])
        reply = f"This uses fictional hospital-list tier {plan['network']}. It does not establish access to any real hospital."
    elif "underwriting" in text or "existing condition" in text or "pre-existing" in text:
        cite("plan.underwriting", plan["underwriting"])
        cite("plan.pre_existing", plan["pre_existing"])
        reply = f"Underwriting: {plan['underwriting'].replace('_', ' ')}. Existing-condition status: {plan['pre_existing']}. No individual condition is assumed covered."
    elif "exclu" in text or "not covered" in text:
        cite("plan.limits", plan["limits"])
        cite("plan.pre_existing", plan["pre_existing"])
        excluded = [care.replace('_', ' ') for care, limit in plan['limits'].items() if not limit]
        reply = "Zero-benefit/excluded categories: "+", ".join(excluded)+f". Existing conditions: {plan['pre_existing']}."
    else:
        care = next((care for care in plan["limits"] if care in text or care.replace('_', ' ') in text), None)
        if not care:
            return unknown
        cite(f"plan.limits.{care}", plan["limits"][care])
        cite("plan.referral", plan["referral"])
        reply = f"{care.replace('_', ' ').capitalize()}: "+(f"{pounds(plan['limits'][care])} annual eligible benefit cap." if plan['limits'][care] else "excluded / no eligible benefit in this snapshot.")+f" {plan['referral']}. This does not decide an individual claim."
    return {"kind": "facts", "reply": reply+" General information, not personal advice.", "citations": citations, "provider_called": False}


class Question(Strict):
    question: str = Field(min_length=1, max_length=1000)


def plan_from_run(db, record, run_id, plan_id):
    run = run_owned(db, record, run_id)
    item = next((item for item in run.data["result"]["items"] if item["id"] == plan_id), None)
    if not item:
        raise HTTPException(404, "Choose a plan in your confirmed comparison")
    return item


@router.post("/runs/{run_id}/plans/{plan_id}/questions")
def question(run_id: str, plan_id: str, body: Question, record=Depends(owned), db: Session = Depends(session)):
    _check_rate_limit('journey-policy:'+record.id+':'+plan_id)
    return answer(plan_from_run(db, record, run_id, plan_id), body.question)


@router.get("/runs/{run_id}/plans/{plan_id}/facts")
def facts(run_id: str, plan_id: str, record=Depends(owned), db: Session = Depends(session)):
    item = plan_from_run(db, record, run_id, plan_id)
    return {"plan": item["plan"], "quote": item["quote"], "scenarios": item["scenarios"]}


@router.get('/runs/{run_id}/plans/{plan_id}/explanation')
def explain(run_id: str, plan_id: str, record=Depends(owned), db: Session = Depends(session)):
    from .explanations import explanation
    return explanation(plan_from_run(db,record,run_id,plan_id),record.version)


@router.post("/runs/{run_id}/plans/{plan_id}/flag-question")
def flag_question(run_id: str, plan_id: str, body: Question, record=Depends(owned), db: Session = Depends(session)):
    plan_from_run(db, record, run_id, plan_id)
    data = dict(record.data)
    questions = list(data.get("flagged_questions", []))
    value = {"question": body.question, "plan_id": plan_id, "profile_version": record.version}
    if value not in questions:
        if len(questions) >= 20:
            raise HTTPException(409, "Up to 20 broker questions may be saved")
        questions.append(value)
    data["flagged_questions"] = questions
    save(db, record, data)
    return {"saved": True, "delivered": False, "notice": "Saved privately. A broker receives it only after your sharing consent and assignment."}
