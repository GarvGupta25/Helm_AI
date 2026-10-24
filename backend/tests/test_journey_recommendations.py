from datetime import date

import pytest

from app.journey.recommendations import compute
from app.journey.schemas import JourneyProfile
from app.research.engine import quote
from app.research.generator import CONFIG, generate
from app.research.schemas import Profile


def filled(**changes):
    data = {"people": [{"relationship": "lead_adult", "age_years": 35}], "location": {"region": "England"},
            "cover": {"start_date": date.today().isoformat()}, "budget": {"choice": "amount", "monthly_pence": 15000},
            "excess": {"choice": "amount", "max_pence": 50000}, "hospital_list": {"choice": "minimum_tier", "minimum_tier": 1},
            "benefits": {"required": []}}
    return JourneyProfile.model_validate({**data, **changes})


def test_engine_replay_family_costs_and_hard_limits():
    plans = generate({**CONFIG, "profiles": 0, "histories": 0})["variants"]
    p = filled()
    a, b = compute(plans, p), compute(plans, p)
    assert a == b
    assert len({item['plan']['family_id'] for item in a['items']}) == 3
    assert a['items'][0]['quote'] == quote(a['items'][0]['plan'], Profile(age=35))
    family = filled(people=[{"relationship": "lead_adult", "age_years": 35}, {"relationship": "partner", "age_years": 60}, {"relationship": "child", "age_years": 8}])
    assert compute(plans, family)['items'][0]['quote']['monthly_pence'] > a['items'][0]['quote']['monthly_pence']
    assert compute(plans, filled(budget={"choice": "amount", "monthly_pence": 0, "strict": True}))['no_fit']
    assert compute(plans, filled(benefits={"required": ['maternity']}))['no_fit']
    result = compute(plans, filled(cover={"start_date": date.today(), "underwriting": "full_medical", "underwriting_required": True}, outpatient={"minimum_annual_pence": 300000, "required": True}))
    assert all(i['plan']['underwriting'] == 'full_medical' and i['plan']['limits']['outpatient'] >= 300000 for i in result['items'])
    with pytest.raises(ValueError):
        compute(plans, JourneyProfile())
