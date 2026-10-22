"""Deterministic fictional UK catalogue and validated quote contracts."""
import re
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator

from .uk import CURRENCY, EXCLUSIONS, IPT_STANDARD_RATE, PROVIDERS, TIME_ZONE

EXCESSES = (0, 10000, 25000, 50000, 100000)
REGIONS = ("London & South East", "South West", "Midlands", "North", "Wales", "Scotland", "Northern Ireland")


def today():
    return datetime.now(ZoneInfo(TIME_ZONE)).date()


def age_on(born: date, day: date):
    return day.year - born.year - ((day.month, day.day) < (born.month, born.day))


class Member(BaseModel):
    dob: date
    child: bool = False
    smoker: bool = False

    @model_validator(mode="after")
    def validate_age(self):
        age = age_on(self.dob, today())
        if age < 0 or age > 110 or (self.child and age > 17) or (not self.child and age < 18):
            raise ValueError("Adults must be 18 or over; children must be 0–17. Date of birth cannot be in the future.")
        return self


class UKQuoteRequest(BaseModel):
    members: list[Member] = Field(min_length=1, max_length=12)
    postcode: str
    start_date: date
    hospital_list: Literal["Standard", "Extended"] = "Standard"
    underwriting: Literal["moratorium", "full_medical_underwriting"] = "moratorium"
    health_consent: bool = False
    medical_history_declared: bool | None = None
    excess_pence: Literal[0, 10000, 25000, 50000, 100000] = 25000
    outpatient: bool = True
    mental_health: bool = False
    digital_gp: bool = False
    six_week_option: bool = False
    ncd_protection: bool = False
    budget_pence: int = Field(default=15000, ge=1000, le=1000000)

    @field_validator("postcode")
    @classmethod
    def validate_postcode(cls, value):
        value = re.sub(r"\s", "", value.upper())
        if not re.fullmatch(r"(?:GIR0AA|[A-Z]{1,2}\d[A-Z\d]?\d[A-Z]{2})", value):
            raise ValueError("Enter a UK postcode, for example SW1A 1AA.")
        return value[:-3] + " " + value[-3:]

    @model_validator(mode="after")
    def validate_request(self):
        if self.members[0].child:
            raise ValueError("The lead applicant must be an adult.")
        if self.start_date < today():
            raise ValueError("Cover cannot start in the past.")
        if self.medical_history_declared is not None and not self.health_consent:
            raise ValueError("Explicit health-data consent is required before medical questions.")
        if self.underwriting == "moratorium" and self.medical_history_declared is not None:
            raise ValueError("Medical answers are not collected for moratorium quotes.")
        return self


def ipt(base_pence: int):
    if base_pence < 0:
        raise ValueError("Premium cannot be negative.")
    return int((Decimal(base_pence) * IPT_STANDARD_RATE).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def region_for(postcode: str):
    prefix = re.match(r"[A-Z]+", postcode).group()
    if prefix == "BT":
        return "Northern Ireland"
    if prefix in {"CF", "NP", "SA", "LL", "LD", "SY"}:
        return "Wales"
    if prefix in {"EH", "G", "AB", "DD", "DG", "FK", "HS", "IV", "KA", "KW", "KY", "ML", "PA", "PH", "TD", "ZE"}:
        return "Scotland"
    if prefix in {"BS", "BA", "BH", "DT", "EX", "GL", "PL", "SN", "SP", "TA", "TQ", "TR"}:
        return "South West"
    if prefix in {"B", "CV", "DE", "DY", "LE", "NG", "NN", "ST", "TF", "WR", "WS", "WV"}:
        return "Midlands"
    if prefix in {"M", "L", "LS", "NE", "S", "YO", "BD", "BL", "CA", "CH", "DH", "DL", "DN", "FY", "HD", "HG", "HU", "HX", "LA", "OL", "PR", "SR", "TS", "WA", "WF", "WN"}:
        return "North"
    return "London & South East"


def catalogue():
    result = []
    for carrier, provider in enumerate(PROVIDERS):
        for tier_index, tier in enumerate(("Essential", "Balanced", "Comprehensive")):
            for network in ("Standard", "Extended"):
                plan_id = f"uk-{carrier + 1}-{tier_index + 1}-{'s' if network == 'Standard' else 'e'}"
                result.append({"id": plan_id, "provider": provider, "tier": tier, "hospital_list": network,
                               "outpatient_limit_pence": (50000, 150000, 300000)[tier_index],
                               "mental_health_sessions": (0, 6, 12)[tier_index], "digital_gp": tier_index > 0,
                               "cancer_level": ("Core", "Extended", "Extended")[tier_index],
                               "excess_options": list(EXCESSES), "not_covered": EXCLUSIONS,
                               "ipid_url": f"/api/uk/plans/{plan_id}/ipid", "version": "demo-1",
                               "demo": True, "carrier_index": carrier, "tier_index": tier_index})
    return result


def base_premium(plan: dict, age: int, region: str, smoker: bool, excess: int):
    """Synthetic rate-card formula, never represented as insurer pricing."""
    age_band = max(0, min(11, (age - 20) // 5))
    base = 2600 + plan["carrier_index"] * 170 + plan["tier_index"] * 1600 + age_band * 580
    base += 900 if plan["hospital_list"] == "Extended" else 0
    factors = {"London & South East": 120, "South West": 102, "Midlands": 100, "North": 95,
               "Wales": 96, "Scotland": 97, "Northern Ireland": 94}
    value = Decimal(base) * Decimal(factors[region]) / 100
    value *= Decimal("1.15") if smoker else 1
    value *= {0: Decimal(1), 10000: Decimal("0.96"), 25000: Decimal("0.90"),
              50000: Decimal("0.82"), 100000: Decimal("0.72")}[excess]
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def demands_and_needs(request: UKQuoteRequest):
    return (f"You asked to compare private medical cover for {len(request.members)} person(s), with a "
            f"{request.hospital_list.lower()} hospital list and a £{request.excess_pence // 100} annual excess per person. "
            f"You selected {request.underwriting.replace('_', ' ')}. "
            f"Outpatient care: {'requested' if request.outpatient else 'not a priority'}; "
            f"mental health: {'requested' if request.mental_health else 'not a priority'}; "
            f"digital GP: {'requested' if request.digital_gp else 'not a priority'}. "
            "Results are a price-sorted fictional comparison, not a personal recommendation. "
            "This statement does not confirm suitability or eligibility. Chronic and pre-existing conditions, "
            "A&E and routine pregnancy care are usually excluded, subject to underwriting and plan wording.")


def quote(request: UKQuoteRequest):
    region = region_for(request.postcode)
    results = []
    for plan in catalogue():
        if plan["hospital_list"] != request.hospital_list:
            continue
        base = sum(base_premium(plan, age_on(member.dob, request.start_date), region, member.smoker, request.excess_pence)
                   for member in request.members)
        if request.six_week_option:
            base = int((Decimal(base) * Decimal("0.9")).quantize(Decimal(1), rounding=ROUND_HALF_UP))
        if request.ncd_protection:
            base += 300 * len(request.members)
        tax = ipt(base)
        gaps = []
        if request.mental_health and not plan["mental_health_sessions"]:
            gaps.append("Mental health sessions are not included.")
        if request.digital_gp and not plan["digital_gp"]:
            gaps.append("Digital GP is not included.")
        if base + tax > request.budget_pence:
            gaps.append("Above your stated monthly budget.")
        results.append({**plan, "premium": {"currency": CURRENCY, "base_monthly_pence": base,
                       "ipt_monthly_pence": tax, "total_monthly_pence": base + tax,
                       "total_annual_pence": (base + tax) * 12, "ipt_rate": str(IPT_STANDARD_RATE)},
                       "excess_pence": request.excess_pence, "gaps": gaps,
                       "why_shown": "Matches your selected hospital list and excess. Review benefit gaps."})
    results.sort(key=lambda plan: (plan["premium"]["total_monthly_pence"], plan["id"]))
    return {"results": results, "demands_and_needs": demands_and_needs(request), "region": region,
            "ranking_basis": "Total monthly price, lowest first; no commission weighting. Benefit gaps are disclosed.",
            "rating_notice": "Synthetic rate card and indicative postcode mapping. No live insurer or address lookup.",
            "demo": True}
