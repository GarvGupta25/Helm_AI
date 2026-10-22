"""Idempotent fictional rate-card seed. Never touches historical tables."""
from itertools import product

from sqlalchemy import insert, select

from .models import UKPlan, UKPremium, UKUnderwritingOption
from .quote import EXCESSES, REGIONS, base_premium, catalogue

AGE_BANDS = [(18, "18–24"), *[(age, f"{age}–{age + 4}") for age in range(25, 70, 5)], (70, "70+")]


def seed(db):
    plans = catalogue()
    for plan in plans:
        existing = db.get(UKPlan, plan["id"])
        if existing is None:
            db.add(UKPlan(id=plan["id"], provider=plan["provider"], tier=plan["tier"],
                          hospital_list=plan["hospital_list"], version=plan["version"], key_facts=plan))
    existing = set(db.scalars(select(UKPremium.id)))
    rows = []
    for plan, (age, age_band), region, smoker, excess in product(plans, AGE_BANDS, REGIONS, (False, True), EXCESSES):
        key = f"{plan['id']}:{age}:{REGIONS.index(region)}:{int(smoker)}:{excess}"
        if key not in existing:
            rows.append({"id": key, "plan_id": plan["id"], "age_band": age_band, "region": region,
                         "smoker": smoker, "excess_pence": excess,
                         "base_monthly_pence": base_premium(plan, age, region, smoker, excess)})
    if rows:
        db.execute(insert(UKPremium), rows)
    for identifier, description in [("moratorium", "Recent-history rules; wording varies by insurer."),
                                    ("full_medical_underwriting", "Health questions before cover, after explicit consent.")]:
        if db.get(UKUnderwritingOption, identifier) is None:
            db.add(UKUnderwritingOption(id=identifier, description=description))
    db.commit()
    return {"plans": len(plans), "new_rates": len(rows), "demo": True}
