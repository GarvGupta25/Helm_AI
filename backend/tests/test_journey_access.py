from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session
from test_journey_compare_api import start
from test_journey_requests import prepare_request
from test_research_api import seed_research

from app.journey.case_models import Grant
from app.models import now


def make_case(client, engine):
    seed_research(engine)
    headers, run = start(client)
    body = prepare_request(client, headers, run)
    case = client.post('/api/journey/quote-requests', headers=headers, json=body).json()
    return headers, body, case


def link_token(client, headers, case):
    response = client.post('/api/journey/access-links', headers=headers, json={'case_id': case['id'], 'hours': 24})
    assert response.status_code == 200, response.text
    inbox = client.get('/api/journey/demo/inbox', headers=headers).json()
    return next(j['content']['url'].split('#')[1] for j in inbox if j['kind'] == 'access_link')


def test_single_purpose_exchange_replay_expiry_revocation_and_csrf(fixture_client):
    client, _, engine = fixture_client
    headers, body, case = make_case(client, engine)
    token = link_token(client, headers, case)
    assert client.post('/api/journey/access-links/exchange', headers={'Origin': 'https://evil.test'}, json={'token': token}).status_code == 403
    response = client.post('/api/journey/access-links/exchange', json={'token': token})
    assert response.status_code == 200, response.text
    assert 'HttpOnly' in response.headers['set-cookie'] and 'SameSite=strict' in response.headers['set-cookie']
    assert client.post('/api/journey/access-links/exchange', json={'token': token}).status_code == 410
    assert client.post('/api/journey/access-links/exchange', json={'token': client.cookies['helm_dashboard']}).status_code == 410
    client.delete('/api/journey/consents/'+body['consent_ids'][0], headers=headers)
    assert client.post('/api/journey/dashboard/logout').status_code == 410
    with Session(engine) as db:
        rows = db.scalars(select(Grant)).all()
        assert all(row.token_hash != token for row in rows)
        assert len(rows) == 2


def test_expired_link_cannot_be_exchanged(fixture_client):
    client, _, engine = fixture_client
    headers, _, case = make_case(client, engine)
    token = link_token(client, headers, case)
    with Session(engine) as db:
        grant = db.scalar(select(Grant).where(Grant.kind == 'magic_link'))
        grant.expires_at = now()-timedelta(seconds=1)
        db.commit()
    assert client.post('/api/journey/access-links/exchange', json={'token': token}).status_code == 410
