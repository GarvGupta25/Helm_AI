from test_journey_recommendations import filled

from app.journey.explanations import band, explanation
from app.journey.recommendations import compute
from app.research.generator import CONFIG, generate


def test_bands_and_frozen_explanations_are_deterministic_and_grounded():
    assert [band(v) for v in [None,0,54.99,55,74.99,75,89.99,90,100]] == ['Not established','Limited','Limited','Fair','Fair','Strong','Strong','Excellent','Excellent']
    plans=generate({**CONFIG,'profiles':0,'histories':0})['variants']
    item=compute(plans,filled())['items'][0]
    result=explanation(item,1)
    assert result == explanation(item,1) and not result['provider_called']
    assert [s['id'] for s in result['sections']] == ['fit','covered','excluded','pay','conditions','hospitals','method']
    assert len(result['sections'][3]['paragraphs']) == 9
    assert all(s['sources'] for s in result['sections'])
    assert 'never assumed covered' in ' '.join(result['sections'][2]['paragraphs'])
    assert 'does not establish waiting periods' in ' '.join(result['sections'][4]['paragraphs'])
