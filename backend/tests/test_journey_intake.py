from sqlalchemy import select

from app.journey.models import JourneySession


def test_draft_confirmation_proposals_and_session_isolation(fixture_client):
    client, _, engine = fixture_client
    created = client.post('/api/journey/sessions').json()
    headers = {'X-Journey-Session': created['session_token']}
    assert created['version'] == 0 and not created['completeness']['ready']
    from sqlalchemy.orm import Session
    with Session(engine) as db:
        assert db.scalar(select(JourneySession)).token_hash != created['session_token']
    assert client.get('/api/journey/profile').status_code == 404
    result = client.post('/api/journey/intake/proposals', headers=headers, json={'field': 'people', 'message': '35', 'expected_revision': 0}).json()
    assert result['draft']['people'][0]['age_years'] == 35
    assert result['profile']['people'] == []
    confirmed = client.post('/api/journey/profile/confirm', headers=headers, json={'expected_version': 0, 'draft_hash': result['draft_hash']}).json()
    assert confirmed['version'] == 1
    assert client.post('/api/journey/profile/confirm', headers=headers, json={'expected_version': 0, 'draft_hash': result['draft_hash']}).status_code == 409
    assert client.post('/api/journey/intake/proposals', headers=headers, json={'field': 'benefits', 'message': 'mental health', 'expected_revision': 1}).status_code == 422
    assert client.post('/api/journey/health-consent', headers=headers, json={'accepted': True}).status_code == 200
    assert client.post('/api/journey/intake/proposals', headers=headers, json={'field': 'benefits', 'message': 'mental health', 'expected_revision': 1}).status_code == 200
