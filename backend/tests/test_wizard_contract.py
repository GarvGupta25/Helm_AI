"""The wizard changes controls, not the existing profile wire contract."""
import json
from datetime import date
from pathlib import Path

from app.journey.intake import propose
from app.journey.schemas import JourneyProfile, completeness


def test_sixty_personas_match_manual_and_guided_canonical_payloads():
    personas = json.loads((Path(__file__).parents[2]/'docs/research/personas.json').read_text())
    assert len(personas) == 60
    for persona in personas:
        source = persona['profile']
        expected = JourneyProfile.model_validate({
            'people': [{'relationship': 'lead_adult', 'age_years': source['age']}],
            'location': {'region': source['region']}, 'cover': {'start_date': date.today()},
            'budget': {'choice': 'amount', 'monthly_pence': source['budget_pence']},
            'excess': {'choice': 'no_preference'}, 'hospital_list': {'choice': 'no_preference'},
            'benefits': {'required': source['required']},
        })
        guided = JourneyProfile()
        for field, text in [('people', str(source['age'])), ('location', source['region']),
                ('cover', date.today().isoformat()), ('budget', str(source['budget_pence']/100)),
                ('excess', 'no preference'), ('hospital_list', 'no preference'),
                ('benefits', ', '.join(source['required']) or 'none')]:
            guided = propose(field, text, guided)
        assert guided.model_dump(mode='json') == expected.model_dump(mode='json'), persona['id']
        assert completeness(guided)['ready']
