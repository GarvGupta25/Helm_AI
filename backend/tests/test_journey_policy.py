import json
from pathlib import Path

import pytest
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


QUESTIONS = json.loads((Path(__file__).parent/'fixtures/policy_questions.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', QUESTIONS, ids=[f'question-{i+1}' for i in range(len(QUESTIONS))])
def test_fifty_policy_questions_have_expected_facts_and_citations(case):
    # Check different synthetic policies, not a provider mock that invents benefits.
    from app.journey.recommendations import EngineProfile
    from app.research.engine import quote
    plans = generate({**CONFIG, 'profiles': 0, 'histories': 0})['variants']
    for index in (0, 38, 207):
        plan = plans[index]
        item = {'id': plan['id'], 'plan': plan, 'quote': quote(plan, EngineProfile())}
        result = answer(item, case['question'])
        assert result['kind'] == case['kind']
        assert result['provider_called'] is False
        for expected in case['fields']:
            assert any(c['field'].startswith(expected) for c in result['citations'])
        for citation in result['citations']:
            assert citation['plan_id'] == plan['id'] and citation['catalogue_version'] == plan['version']
            if citation['field'].startswith('scenario.'):
                continue
            source = item
            for part in citation['field'].split('.'):
                source = source[part]
            assert citation['value'] == source
        if case['kind'] == 'unknown':
            assert not result['citations'] and 'not' in result['reply']
