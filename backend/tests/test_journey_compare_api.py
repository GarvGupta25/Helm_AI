from test_journey_recommendations import filled
from test_research_api import seed_research

from app.public_assistant import _rate_store


def start(client, profile=None):
    _rate_store.clear()
    created = client.post('/api/journey/sessions').json()
    headers = {'X-Journey-Session': created['session_token']}
    client.post('/api/journey/health-consent', headers=headers, json={'accepted': True})
    draft = client.patch('/api/journey/intake/draft', headers=headers, json={'expected_revision': 0, 'profile': (profile or filled()).model_dump(mode='json')}).json()
    confirmed = client.post('/api/journey/profile/confirm', headers=headers, json={'expected_version': 0, 'draft_hash': draft['draft_hash']})
    assert confirmed.status_code == 200, confirmed.text
    response = client.post('/api/journey/recommendations', headers=headers)
    assert response.status_code == 200, response.text
    return headers, response.json()


def test_current_run_shortlist_ownership_and_preview(fixture_client):
    client, _, engine = fixture_client
    seed_research(engine)
    headers, run = start(client)
    assert len(run['items']) == 3
    item = run['items'][0]['id']
    assert client.put('/api/journey/shortlist', headers=headers, json={'run_id': run['run_id'], 'expected_version': 1, 'plan_ids': [item]}).status_code == 200
    assert client.put('/api/journey/shortlist', headers=headers, json={'run_id': run['run_id'], 'expected_version': 1, 'plan_ids': [item, item]}).status_code == 422
    preview = client.post(f"/api/journey/runs/{run['run_id']}/what-if", headers=headers, json=filled(benefits={'required': ['maternity']}).model_dump(mode='json')).json()
    assert preview['result']['no_fit'] and preview['profile_unchanged']
    other, _ = start(client)
    assert client.get(f"/api/journey/runs/{run['run_id']}", headers=other).status_code == 404
    assert client.get('/api/journey/profile', headers=headers).json()['version'] == 1
