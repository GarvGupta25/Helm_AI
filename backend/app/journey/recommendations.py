from copy import deepcopy
from datetime import date, datetime, time, timezone

from pydantic import Field

from ..research.engine import recommend
from ..research.schemas import Evidence, Profile
from .schemas import JourneyProfile, completeness


class EngineProfile(Profile):
    adult_ages: list[int] = Field(default_factory=list)
    budget_enabled: bool = True


def age(person, on):
    born = person.date_of_birth
    return (on.year-born.year-((on.month, on.day) < (born.month, born.day))) if born else person.age_years


def compute(plans, profile: JourneyProfile, limit=3):
    check = completeness(profile)
    if not check["ready"]:
        raise ValueError("Complete and confirm all mandatory fields first")
    start = profile.cover.start_date or date.today()
    adult_ages = [age(p, start) for p in profile.people if p.relationship != "child"]
    child_ages = [age(p, start) for p in profile.people if p.relationship == "child"]
    if any(a is None or not 18 <= a <= 85 for a in adult_ages) or any(a is None or not 0 <= a <= 17 for a in child_ages):
        raise ValueError("A household member is outside the supported age range on the start date")
    values = {"age": adult_ages[0], "adult_ages": adult_ages, "adults": len(adult_ages), "children": len(child_ages),
        "region": profile.location.region, "budget_pence": profile.budget.monthly_pence if profile.budget.choice == "amount" else 1000000,
        "budget_enabled": profile.budget.choice == "amount", "strict_budget": profile.budget.strict and profile.budget.choice == "amount",
        "excess_max_pence": profile.excess.max_pence if profile.excess.choice == "amount" else 50000,
        "strict_excess": profile.excess.strict and profile.excess.choice == "amount", "network_min": profile.hospital_list.minimum_tier or 1,
        "required": profile.benefits.required or [], "preferred": profile.benefits.preferred,
        "existing_condition": profile.health.existing_condition_scenario == "yes"}
    values["evidence"] = {field: Evidence(value=value) for field, value in values.items() if isinstance(value, (str, int, bool))}
    engine_profile = EngineProfile(**values)
    eligible, rejected = [], []
    for original in plans:
        plan = deepcopy(original)
        plan["source_plan_id"] = plan["id"]
        plan["id"] += "@journey-family-v1"
        plan["version"] += "-journey-family-v1"
        plan["family_terms"] = {"source": "fictional-demo-extension-v1", "adults": "1–2, ages 18–85", "children": "0–6, ages 0–17",
            "rating": "Sum adult age factors; each child costs 35% of lead adult factor. No individual medical underwriting."}
        failed = []
        if any(not plan["age_min"] <= a <= plan["age_max"] for a in adult_ages):
            failed.append({"field": "people", "reason": "An adult is outside this synthetic plan's age range", "clause_id": None})
        if profile.cover.underwriting_required and plan["underwriting"] != profile.cover.underwriting:
            failed.append({"field": "underwriting", "reason": "Does not meet the confirmed underwriting method", "clause_id": f"{plan['id']}:field:underwriting"})
        if profile.outpatient.required and plan["limits"]["outpatient"] < profile.outpatient.minimum_annual_pence:
            failed.append({"field": "outpatient", "reason": "Annual outpatient limit is below the confirmed minimum", "clause_id": f"{plan['id']}:outpatient"})
        if failed:
            rejected.append({"id": plan["id"], "reasons": failed})
        else:
            eligible.append(plan)
    result = recommend(eligible, engine_profile, as_of=datetime.combine(start, time.min, tzinfo=timezone.utc), limit=limit)
    result["rejected"].extend(rejected)
    result["profile_snapshot"] = profile.model_dump(mode="json")
    result["engine_version"] = "journey-deterministic-v1"
    result["rating_date"] = start.isoformat()
    result["catalogue_version"] = (plans[0]["version"] if plans else "unavailable")+"-journey-family-v1"
    result["assumptions"] = "Fictional family terms: individually age-rated adults; each child adds 35% of the lead adult factor. Children are not individually medically underwritten. 12% synthetic IPT assumption. No real offer."
    return result
