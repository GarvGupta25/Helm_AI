from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import Session

from app.market.models import UKPlan, UKPremium
from app.market.seed import seed
from app.servicing import evaluate_uk_claim


def test_migration_round_trip_and_idempotent_seed(tmp_path):
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    url = f"sqlite:///{(tmp_path / 'migration.db').as_posix()}"
    config.attributes["connection_url"] = url
    command.upgrade(config, "head")
    engine = create_engine(url)
    assert "uk_plan" in inspect(engine).get_table_names()
    with Session(engine) as db:
        first = seed(db)
        assert first["new_rates"] == 23100
        assert seed(db)["new_rates"] == 0
        assert db.scalar(select(func.count()).select_from(UKPlan)) == 30
        assert db.scalar(select(func.count()).select_from(UKPremium)) == 23100
    command.downgrade(config, "base")
    assert "uk_plan" not in inspect(engine).get_table_names()
    engine.dispose()


def claim(**changes):
    return evaluate_uk_claim(**{"amount_pence": 100000, "excess_pence": 25000,
                               "excess_used_pence": 0, "benefit_remaining_pence": 50000,
                               "pre_authorised": True, "acute": True, **changes})


def test_deterministic_excess_and_limits():
    result = claim()
    assert result["plan_pays_pence"] == 50000
    assert result["member_pays_pence"] == 50000
    assert claim(benefit_remaining_pence=100000)["plan_pays_pence"] == 75000
    assert claim(excess_used_pence=25000, benefit_remaining_pence=100000)["plan_pays_pence"] == 100000
    assert claim(amount_pence=1000)["outcome"] == "within_excess"


@pytest.mark.parametrize("changes,outcome", [({"emergency": True}, "nhs_signposting"),
    ({"pre_authorised": False}, "requires_pre_authorisation"), ({"acute": False}, "excluded"),
    ({"history_exclusion_uncertain": True}, "manual_review")])
def test_routing_never_lets_an_agent_adjudicate(changes, outcome):
    assert claim(**changes)["outcome"] == outcome
    assert claim(**changes)["plan_pays_pence"] == 0


@pytest.mark.parametrize("changes", [{"amount_pence": -1}, {"amount_pence": 0.5},
    {"amount_pence": True}, {"excess_used_pence": 26000}])
def test_invalid_financial_inputs(changes):
    with pytest.raises(ValueError):
        claim(**changes)
