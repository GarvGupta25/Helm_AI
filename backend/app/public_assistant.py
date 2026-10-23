"""Public UK guidance with fixed safety routes. Raw text never leaves the session."""
import re
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from .market.models import UKAudit, UKSupportTicket
from .market.uk import IPT_STANDARD_RATE

_rate_store: dict[str, deque] = defaultdict(deque)
_rate_lock = Lock()
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 3600
INFORMATION = " This is general information, not advice."
FALLBACK = "I’m Helm’s AI assistant for UK private medical cover. Try our FAQs or glossary, or explore the quote comparison. I can explain the basics. This is a demo with no live adviser service."
EMERGENCY = "If this is a medical emergency, call 999 or go to your nearest A&E now. For urgent advice that isn’t an emergency, use NHS 111. Private cover doesn’t replace emergency NHS care."
CRISIS = "I’m sorry you’re going through this. If you’re in immediate danger, call 999 or go to A&E now. If you can, reach out to someone you trust and ask them to stay with you. You deserve support. Please seek urgent help from NHS services. We can pause the insurance conversation."
KNOWLEDGE = {
    "ipt": f"Insurance Premium Tax is a tax on insurance premiums. The standard rate used here is {(IPT_STANDARD_RATE * 100).normalize():f}%. Quote totals include it; base premium and tax are shown separately." + INFORMATION,
    "excess": "An excess is the amount you pay towards eligible treatment. Check whether it applies per person, claim or policy year. The demo uses an annual excess per person." + INFORMATION,
    "underwriting": "Moratorium applies rules to recent medical history, which may be checked when you claim. Full medical underwriting asks questions before cover starts and sets out specific exclusions. Neither guarantees cover for an existing condition." + INFORMATION,
    "exclusions": "Private medical insurance usually covers eligible acute conditions. Chronic and pre-existing conditions, A&E and routine pregnancy care are usually excluded, depending on underwriting and policy terms. I cannot decide whether a condition or treatment is covered." + INFORMATION,
    "claims": "I cannot guarantee a claim or decide a coverage dispute. Check the policy, get pre-authorisation before planned treatment, and ask the insurer for written reasons if you disagree with a decision. You can use its complaints process." + INFORMATION,
    "cover": "Private medical insurance is optional and complements NHS care. It may pay for eligible private diagnosis and treatment of acute conditions. Check the hospital list, excess, limits and exclusions before deciding." + INFORMATION,
    "cooling_off": "Real PMI contracts generally offer a 14-day cancellation period. Check approved terms for when the period starts and any charges or refund rules." + INFORMATION,
}


def _check_rate_limit(ip: str):
    now = time.monotonic()
    with _rate_lock:
        for key in list(_rate_store):
            while _rate_store[key] and _rate_store[key][0] <= now - RATE_LIMIT_WINDOW_SECONDS:
                _rate_store[key].popleft()
            if not _rate_store[key]:
                del _rate_store[key]
        if len(_rate_store) >= 10000 and ip not in _rate_store:
            raise HTTPException(429, "The assistant is busy. Please try again later.")
        queue = _rate_store[ip]
        if len(queue) >= RATE_LIMIT_REQUESTS:
            raise HTTPException(429, "You’ve reached the message limit. Please try again in an hour.")
        queue.append(now)


class PublicAssistantRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, value):
        value = value.strip()
        if not value or len(value) > 500:
            raise ValueError("Enter a message between 1 and 500 characters.")
        return value


class PublicAssistantResponse(BaseModel):
    reply: str
    intent: str = "information"
    ticket_ref: str | None = None
    transcript_ref: str | None = None


def classify_and_reply(message: str):
    text = message.casefold().replace('’', "'")
    routes = [
        (r"chest pain|can'?t breathe|cannot breathe|heart attack|stroke|unconscious|severe bleeding|overdose", EMERGENCY, "emergency", False),
        (r"end it all|kill myself|suicid|self.harm|hurt myself|don't want to live|do not want to live", CRISIS, "self_harm", False),
        (r"(?:\d[ -]?){13,19}|\b[A-CEGHJ-PR-TW-Z]{2}\s?\d{6}\s?[A-D]\b|password\s*[:=]|one.time.code|\b\d{2}-\d{2}-\d{2}\b", "Please don’t share card, bank, identity details, passwords or one-time codes here. They have not been sent to an AI model or stored in server conversation logs. Your browser tab may retain the visible conversation until you clear it.", "sensitive_data", False),
        (r"complain|ombudsman|legal action|sue you", "I’m sorry something has gone wrong. I can create a demo support reference. For a real policy, contact the responsible firm’s complaints team. Our Complaints page explains the Financial Ombudsman Service route. No live adviser response is promised by this demo.", "complaint", True),
        (r"husband.*died|wife.*died|bereav|confused|struggling|hardship|can't afford|cannot afford|vulnerab", "We can slow down. You don’t have to decide now. Our Extra support page explains ways to get help. I can create a demo support reference; no live callback service is connected. Please don’t share health or financial details here.", "vulnerability", True),
        (r"adviser|advisor|human|speak to|call me|callback|claim.*disput|appeal", "I can create a demo support reference and point you to Contact or Extra support. A live adviser service is not connected. For a real policy, use the verified contact details of your insurer or adviser.", "handoff", True),
        (r"ignore.*instruction|system prompt|developer message|jailbreak|pretend.*authori|bypass|override", FALLBACK, "prompt_injection", False),
        (r"best.*(?:me|plan|insur)|recommend|should i|right for me|you should buy", "I can’t recommend a plan in chat. Compare hospital access, excess, benefits, exclusions and budget. Use the quote journey for a needs-based comparison or ask a qualified human adviser for advice.", "advice_request", False),
        (r"dubai|\buae\b|\baed\b|emirates?|\+971", "I can help with UK private medical insurance only. In the UK, private cover is optional and complements the NHS. Explore the UK guides or quote comparison." + INFORMATION, "market_scope", False),
        (r"price|premium|quote|cost.*month|how much", "I can’t give a price without a quote. Use Get a quote for the server-calculated demo comparison. It shows the base premium, tax and total, with exclusions beside benefits.", "start_quote", False),
        (r"diabet|asthma|cancer|cover my|my condition|my diagnosis|chronic|pre.existing|not covered|isn't covered|is not covered|pregnan", KNOWLEDGE["exclusions"], "exclusions", False),
        (r"treat|diagnos|symptom|medicat|medical advice", "I can explain insurance terms, but I can’t diagnose or suggest treatment. Speak to a qualified healthcare professional. For an emergency call 999 or go to A&E; for urgent non-emergency advice use NHS 111.", "medical_question", False),
        (r"cymraeg|welsh|bore da|bonjour|hola|नमस्ते|مرحبا", "I can currently provide reviewed information in English only. Extra support explains language-support requirements. A live interpreter or adviser service is not connected.", "language", False),
    ]
    for pattern, reply, intent, handoff in routes:
        if re.search(pattern, text, re.I):
            return reply, intent, handoff
    for topic, pattern in [("ipt", r"\bipt\b|tax"), ("excess", r"excess|deductible|co.pay"),
                           ("underwriting", r"moratorium|underwrit|waiting"), ("claims", r"claim|guarantee"),
                           ("cooling_off", r"cancel|cooling"), ("cover", r"private health|insurance|cover work")]:
        if re.search(pattern, text):
            return KNOWLEDGE[topic], topic, False
    return FALLBACK, "out_of_scope", False


def output_is_safe(reply: str):
    return not re.search(r"you should buy|best for you|i recommend|guarantee.*paid|\baed\b|\buae\b|dubai|\+971|https?://|www\.", reply, re.I)


async def handle_public_assistant(body: PublicAssistantRequest, request: Request, db: Session):
    _check_rate_limit(request.client.host if request.client else "unknown")
    reply, intent, handoff = classify_and_reply(body.message)
    if not output_is_safe(reply):
        reply, intent, handoff = FALLBACK, "output_filter", True
    audit = UKAudit(intent=intent, event={"model": "reviewed-knowledge-v1", "raw_text_retained": False,
                                        "tools": ["retrieve_uk_knowledge"], "guardrail": intent})
    db.add(audit)
    db.flush()
    ticket = None
    if handoff:
        ticket = UKSupportTicket(reason=intent, transcript_ref=audit.id,
                                 summary=f"Demo {intent} request. Raw text and health details not retained.")
        db.add(ticket)
        db.flush()
    db.commit()
    return PublicAssistantResponse(reply=reply, intent=intent, transcript_ref=audit.id,
                                   ticket_ref=ticket.id if ticket else None)
