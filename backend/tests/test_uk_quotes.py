from datetime import timedelta

import pytest
from pydantic import ValidationError

from app.market.quote import UKQuoteRequest, catalogue, ipt, quote, today


def payload(**changes):
    return {"members": [{"dob": "1990-04-12"}], "postcode": "SW1A 1AA", "start_date": today().isoformat(), **changes}


def test_catalogue_and_tax_rounding():
    assert len(catalogue()) == 30
    assert len({plan["id"] for plan in catalogue()}) == 30
    assert ipt(5) == 1
    assert ipt(5420) == 650
    with pytest.raises(ValueError):
        ipt(-1)


def test_pricing_is_integer_reconciled_sorted_and_discloses_gaps():
    result = quote(UKQuoteRequest(**payload(mental_health=True, budget_pence=1000)))
    assert len(result["results"]) == 15
    prices = []
    for plan in result["results"]:
        premium = plan["premium"]
        assert premium["currency"] == "GBP"
        assert premium["total_monthly_pence"] == premium["base_monthly_pence"] + premium["ipt_monthly_pence"]
        assert premium["total_annual_pence"] == premium["total_monthly_pence"] * 12
        assert isinstance(premium["total_monthly_pence"], int)
        assert plan["gaps"]
        prices.append(premium["total_monthly_pence"])
    assert prices == sorted(prices)
    assert "not a personal recommendation" in result["demands_and_needs"]


@pytest.mark.parametrize("changes", [
    {"postcode": "not a postcode"}, {"members": [{"dob": "2020-01-01"}]},
    {"members": [{"dob": "2999-01-01"}]}, {"start_date": (today() - timedelta(days=1)).isoformat()},
    {"medical_history_declared": True, "health_consent": False},
    {"members": [{"dob": "1990-01-01", "child": True}]}, {"excess_pence": 123},
])
def test_invalid_answers_rejected(changes):
    with pytest.raises(ValidationError):
        UKQuoteRequest(**payload(**changes))


def test_quote_confirmation_capability_and_consents(fixture_client):
    client, _, _ = fixture_client
    response = client.post("/api/uk/quotes", json=payload())
    assert response.status_code == 200, response.text
    data = response.json()
    token = data["quote_id"]
    assert client.get("/api/uk/quotes/current", headers={"X-Quote-Token": "bad"}).status_code == 404
    assert client.get("/api/uk/quotes/current", headers={"X-Quote-Token": token}).status_code == 200
    body = {"plan_id": data["results"][0]["id"], "understood_exclusions": True,
            "accepted_status": True, "received_ipid": True, "test_payment": True}
    assert client.post("/api/uk/quotes/confirm", json={**body, "test_payment": False}, headers={"X-Quote-Token": token}).status_code == 422
    result = client.post("/api/uk/quotes/confirm", json=body, headers={"X-Quote-Token": token})
    assert result.status_code == 200, result.text
    assert result.json()["paid_pence"] == 0
    assert client.post("/api/uk/quotes/confirm", json=body, headers={"X-Quote-Token": token}).json() == result.json()
    body["plan_id"] = data["results"][1]["id"]
    assert client.post("/api/uk/quotes/confirm", json=body, headers={"X-Quote-Token": token}).status_code == 409
