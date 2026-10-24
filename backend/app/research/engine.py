"""Deterministic, clause-grounded synthetic comparison. All amounts integer pence."""
import math
import random
import re
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from .generator import CONFIG
from .schemas import Profile

SCENARIOS = {
    "low_usage": {"diagnostics": 20000},
    "moderate": {"diagnostics": 80000, "outpatient": 120000},
    "outpatient_heavy": {"outpatient": 400000, "physio": 100000},
    "mental_health": {"mental_health": 240000},
    "eligible_surgery": {"inpatient": 2000000},
    "condition_excluded": {"pre_existing": 600000},
}


def rounded(value):
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def quote(plan, profile):
    # Labelled assumptions, not a clinically/actuarially calibrated model.
    age_factor = Decimal("1.018") ** (profile.age - 18)
    region = Decimal("1.20") if profile.region == "London" else Decimal("1")
    household = Decimal(profile.adults) + Decimal("0.35") * profile.children
    if getattr(profile, "adult_ages", None):
        household = (sum(Decimal("1.018") ** (age-18) for age in profile.adult_ages)
                     + Decimal("0.35")*profile.children*age_factor)/age_factor
    excess_factor = Decimal("1") - Decimal(plan["excess_pence"]) / Decimal("250000")
    base = rounded(Decimal(plan["base_pence"]) * age_factor * region * household * excess_factor)
    tax = rounded(Decimal(base) * Decimal(".12"))
    return {"base_pence": base, "tax_pence": tax, "monthly_pence": base+tax, "annual_pence": (base+tax)*12,
            "assumptions": "Synthetic age/region/household formula, 12% IPT assumption; no real offer."}


def filter_plan(plan, profile, as_of=None):
    failed = []
    now = as_of or datetime.now(timezone.utc)
    try:
        available = datetime.fromisoformat(plan["valid_from"]) <= now < datetime.fromisoformat(plan["valid_until"])
    except (ValueError, KeyError):
        available = False
    if not available:
        failed.append({"field": "validity", "reason": "Synthetic variant is outside its documented validity period or evidence is missing", "clause_id": None})
    if profile.region not in plan["regions"] or not plan["age_min"] <= profile.age <= plan["age_max"]:
        failed.append({"field": "availability", "reason": "Age or region outside synthetic offer bounds", "clause_id": None})
    for care in set(profile.required):
        status = plan.get("pre_existing", "unknown") if care == "pre_existing" else ("covered" if plan["limits"].get(care, 0) > 0 else "excluded")
        if status != "covered":
            failed.append({"field": care, "reason": f"Required benefit {status}; no verified coverage for this need", "clause_id": f"{plan['id']}:{care}"})
    if profile.existing_condition and profile.required:
        failed.append({"field": "pre_existing", "reason": f"Required treatment for existing condition: {plan['pre_existing']}; headline benefits do not establish cover", "clause_id": f"{plan['id']}:pre_existing"})
    price = quote(plan, profile)
    for violated, field, reason in [
        (profile.strict_budget and price["monthly_pence"] > profile.budget_pence, "budget", "Premium exceeds confirmed strict budget"),
        (profile.strict_excess and plan["excess_pence"] > profile.excess_max_pence, "excess", "Excess exceeds confirmed ceiling"),
        (plan["network"] < profile.network_min, "network", "Required hospital tier unavailable"),
    ]:
        if violated:
            failed.append({"field": field, "reason": reason, "clause_id": None})
    return failed


def scenario(plan, expenses):
    eligible, uncovered = 0, 0
    details = []
    for care, bill in expenses.items():
        allowed = min(bill, plan["limits"].get(care, 0))
        eligible += allowed
        uncovered += bill - allowed
        details.append({"care": care, "bill_pence": bill, "eligible_pence": allowed,
                        "uncovered_pence": bill-allowed, "clause_id": f"{plan['id']}:{care}"})
    excess = min(eligible, plan["excess_pence"])
    copay = rounded((eligible-excess) * plan["copay"])
    return {"eligible_pence": eligible, "uncovered_pence": uncovered, "excess_pence": excess,
            "copay_pence": copay, "member_pence": uncovered+excess+copay,
            "insurer_pence": eligible-excess-copay, "details": details,
            "assumptions": "One adult, new eligible acute treatment, referral/authorisation satisfied, annual caps/excess; no maximum loss guarantee."}


def simulation(plan, draws=500):
    rng = random.Random(CONFIG["seed"])
    # Same utilization draws for every policy, deterministic and independent of rank.
    totals = []
    names = list(SCENARIOS)
    for _ in range(draws):
        costs = SCENARIOS[rng.choice(names)]
        multiplier = rng.uniform(.7, 1.3)
        totals.append(scenario(plan, {k: rounded(v*multiplier) for k, v in costs.items()})["member_pence"])
    totals.sort()
    return {"draws": draws, "mean_pence": rounded(sum(totals)/draws), "median_pence": totals[draws//2],
            "p90_pence": totals[math.ceil(draws*.9)-1], "assumptions": "Equal-weight fictional care scenarios; not estimated real utilization probabilities."}


def weighted(components, weights):
    known = {key: weight for key, weight in weights.items() if components.get(key) is not None}
    total = sum(known.values())
    contributions = {k: round(components[k]*w/total, 6) for k, w in known.items()} if total else {}
    return {"score": round(sum(contributions.values()), 4), "components": components,
            "contributions": contributions, "completeness": total/sum(weights.values())}


def standard(plan):
    ref = quote(plan, Profile(age=35, region="England"))["monthly_pence"]
    components = {
        "coverage": sum(min(plan["limits"][c]/cap, 1) for c, cap in [("inpatient", 10000000), ("cancer", 10000000), ("outpatient", 500000), ("mental_health", 150000), ("diagnostics", 400000), ("physio", 50000)]) / 6 * 100,
        "reference_value": max(0, 100-ref/300),
        "access": 60 if plan["network"] == 1 else 100,
        "transparency": 90 if plan["pre_existing"] == "excluded" else 70,
        "service": plan.get("service_simulated"), "flexibility": 80,
    }
    return weighted(components, CONFIG["standard_weights"])


def contextual(plan, profile, memory=None, as_of=None):
    priorities = list(set(profile.required + profile.preferred))
    # Memory can fill an absent soft preference only; never alter current constraints.
    remembered = [m for m in (memory or []) if m.get("field") == "preferred" and not profile.preferred and not profile.required]
    if remembered:
        priorities = list(set(remembered[-1]["value"]))
    coverage_fit = 100*sum(plan["limits"].get(c, 0) > 0 for c in priorities)/len(priorities) if priorities else 50
    history_strength = 0
    if remembered:
        observed = remembered[-1].get("observed_at")
        age_days = max(0, ((as_of or datetime.now(timezone.utc))-datetime.fromisoformat(observed)).total_seconds()/86400) if observed else 0
        history_strength = .2*max(0, 1-age_days/CONFIG["memory_days"])
        coverage_fit = 50+(coverage_fit-50)*history_strength
    premium = quote(plan, profile)["monthly_pence"]
    components = {
        "coverage": coverage_fit,
        "budget": max(0, 100-100*max(0, premium-profile.budget_pence)/max(1, profile.budget_pence)) if getattr(profile, "budget_enabled", True) else None,
        "underwriting": 0 if profile.existing_condition else 60,
        "excess": max(0, 100-100*max(0, plan["excess_pence"]-profile.excess_max_pence)/50000),
        "access": 100 if plan["network"] >= profile.network_min else 0,
        "preferences": 100-plan["copay"]*100,
    }
    result = weighted(components, CONFIG["context_weights"])
    result["history_used"] = remembered
    result["history_strength"] = round(history_strength, 6)
    result["anti_double_counting"] = "Dialogue/history supply preference evidence only; no separate additive reward."
    return result


def recommend(plans, profile, memory=None, as_of=None, limit=3):
    rejected, eligible = [], []
    clock = as_of or datetime.now(timezone.utc)
    completeness = len([v for v in profile.evidence.values() if v.confirmed and v.source == "current_explicit"])
    alpha = CONFIG["alpha"][0] if completeness < 3 else CONFIG["alpha"][1] if completeness < 6 else CONFIG["alpha"][2]
    for plan in plans:
        failures = filter_plan(plan, profile, clock)
        if failures:
            rejected.append({"id": plan["id"], "reasons": failures})
            continue
        s, c = standard(plan), contextual(plan, profile, memory, clock)
        score = round(alpha*s["score"]+(1-alpha)*c["score"], 4)
        eligible.append({"id": plan["id"], "plan": plan, "quote": quote(plan, profile), "standard": s,
                         "contextual": c, "alpha": alpha, "fusion": score,
                         "uncertainty": ["Synthetic data; not validated for real customers", "Existing-condition eligibility unknown until underwriting"],
                         "evidence_ids": [f"{plan['id']}:{care}" for care in set(profile.required+profile.preferred)],
                         "scenarios": {key: {**scenario(plan, value),
                                            "annual_total_pence": quote(plan, profile)["annual_pence"]+scenario(plan, value)["member_pence"]}
                                       for key, value in SCENARIOS.items()}})
    eligible.sort(key=lambda p: (-p["fusion"], p["quote"]["monthly_pence"], p["id"]))
    chosen, families = [], set()
    for item in eligible:
        family = item["plan"]["family_id"]
        if family not in families:
            chosen.append(item)
            families.add(family)
        if len(chosen) == 3:
            break
    diverse = list(chosen)
    if limit > 3:
        chosen.extend(item for item in eligible if item not in diverse)
    chosen = chosen[:limit]
    for item in chosen[:3]:
        item["simulation"] = simulation(item["plan"])
        item["stability"] = {"fusion_alpha_minus_05": round(max(.2, alpha-.05)*item["standard"]["score"]+(1-max(.2, alpha-.05))*item["contextual"]["score"], 4),
                             "fusion_alpha_plus_05": round(min(.8, alpha+.05)*item["standard"]["score"]+(1-min(.8, alpha+.05))*item["contextual"]["score"], 4)}
    return {"source": "synthetic", "model_version": CONFIG["version"], "alpha": alpha,
            "items": chosen, "rejected": rejected, "eligible_count": len(eligible),
            "alternatives": [{"id": p["id"], "standard": p["standard"]["score"], "contextual": p["contextual"]["score"],
                              "fusion": p["fusion"], "quote": p["quote"], "evidence_ids": p["evidence_ids"]}
                             for p in eligible if p not in chosen],
            "selection": "Score order with at most one variant per family. No silent constraint relaxation.",
            "no_fit": not chosen, "memory_used": any(p["contextual"]["history_used"] for p in chosen),
            "memory_as_of": clock.isoformat() if any(p["contextual"]["history_used"] for p in chosen) else None}


def extract(message):
    text = message.casefold()
    if re.search(r"ignore|system prompt|override|jailbreak|<script", text):
        return {"proposed": {}, "safety": "untrusted_instruction", "question": "Use the preference controls to make a change."}
    changes = {}
    operations = []
    if re.search(r"rather than|instead of", text):
        return {"proposed": {}, "question": "Which benefit should be removed, and which should be added? Use the controls to confirm each change.", "source_quote": message, "confidence": .4}
    budget = re.search(r"(?:budget(?: of)?|pay|afford)\s*(?:up to\s*)?£?\s*(\d+(?:\.\d{1,2})?)", text)
    if not budget and "excess" not in text:
        budget = re.search(r"£\s*(\d+(?:\.\d{1,2})?)", text)
    if budget:
        changes["budget_pence"] = rounded(float(budget.group(1))*100)
        changes["strict_budget"] = bool(re.search(r"strict|cannot exceed|can't exceed|maximum budget", text))
    excess = re.search(r"excess\s*(?:below|under|of|maximum|up to)?\s*£?\s*(\d+)", text)
    if excess:
        changes["excess_max_pence"] = int(excess.group(1))*100
        changes["strict_excess"] = bool(re.search(r"must|below|under|maximum|essential", text))
    cares = [care for care, pattern in [("mental_health", "mental health|therapy"), ("physio", "physio"), ("outpatient", "outpatient"), ("cancer", "cancer"), ("dental", "dental"), ("maternity", "maternity")] if re.search(pattern, text)]
    if cares:
        field = "required" if re.search(r"must|essential|required|mandatory", text) else "preferred"
        changes[field] = cares
        operations.append({"field": field, "op": "add", "values": cares})
    if re.search(r"remove|forget|don't need|do not need", text) and cares:
        changes.update(required=[], preferred=[])
        operations = [{"field": field, "op": "remove", "values": cares} for field in ("required", "preferred")]
    if "flexible" in text and "budget" in text:
        changes["strict_budget"] = False
    if "hospital" in text and re.search(r"broad|best|wider", text):
        changes["network_min"] = 2
    if re.search(r"surprise|predictab", text) and not excess:
        return {"proposed": changes, "question": "What maximum excess would you be comfortable paying?", "source_quote": message, "confidence": .6}
    return {"proposed": changes, "operations": operations, "source_quote": message, "confidence": .9 if changes else .3,
            "question": "Confirm these changes before reranking." if changes else "Which budget, excess or benefit would you like to change?",
            "extractor": "deterministic-ontology-v1"}
