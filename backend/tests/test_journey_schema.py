from datetime import date

import pytest
from pydantic import ValidationError

from app.journey.schemas import JourneyProfile, Person, completeness


def test_unanswered_is_not_a_default_quote():
    assert len(completeness(JourneyProfile())["missing"]) == 7
    p = JourneyProfile(people=[{"relationship": "lead_adult", "age_years": 35}], location={"region": "England"},
                       cover={"start_date": date.today()}, budget={"choice": "no_target"}, excess={"choice": "no_preference"},
                       hospital_list={"choice": "no_preference"}, benefits={"required": []})
    assert completeness(p)["ready"]
    assert p.budget.monthly_pence is None


def test_age_bounds_roles_and_unknown_fields():
    for fields in ({"relationship": "child", "age_years": 20}, {"relationship": "lead_adult", "age_years": 4}):
        with pytest.raises(ValidationError):
            Person(**fields)
    with pytest.raises(ValidationError):
        JourneyProfile(prices={"monthly": 1})
    with pytest.raises(ValidationError):
        JourneyProfile(benefits={"required": ["cancer"], "preferred": ["cancer"]})
