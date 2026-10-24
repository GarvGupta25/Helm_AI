from datetime import date

from test_journey_recommendations import filled

from app.journey.policy import answer
from app.journey.recommendations import compute
from app.research.generator import CONFIG, generate


def test_policy_facts_unknown_refusal_and_server_scenario():
    plans = generate({**CONFIG, "profiles": 0, "histories": 0})['variants']
    item = compute(plans, filled())['items'][0]
    result = answer(item, 'Break down my premium')
    assert result['kind'] == 'facts'
    assert next(c for c in result['citations'] if c['field'] == 'quote.monthly_pence')['value'] == item['quote']['monthly_pence']
    assert answer(item, 'Are my dental implants guaranteed covered?')['kind'] == 'unknown'
    scenario = answer(item, 'What would I pay in the mental health scenario?')
    assert scenario['citations'][0]['value']['member_pence'] == item['scenarios']['mental_health']['member_pence']
    assert date.today().isoformat()
