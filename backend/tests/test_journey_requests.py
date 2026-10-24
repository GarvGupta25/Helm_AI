from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_journey_compare_api import start
from test_research_api import seed_research

from app.journey.case_models import Case, QuoteRequest


def prepare_request(client, headers, run):
    contact = client.post('/api/journey/contacts/challenges', headers=headers, json={'channel': 'email', 'destination': 'request@example.test', 'demo_acknowledged': True}).json()['contact_id']
    inbox = client.get('/api/journey/demo/inbox', headers=headers).json()
    code = next(j['content']['code'] for j in inbox if j['contact_id'] == contact)
    client.post('/api/journey/contacts/verify', headers=headers, json={'contact_id': contact, 'code': code})
    items = run['items']
    consent = client.post('/api/journey/consents', headers=headers, json={'purpose': 'insurer_share', 'recipients': sorted({i['plan']['insurer_id'] for i in items}), 'accepted': True, 'wording_version': 'journey-sharing-v1'}).json()
    return {'run_id': run['run_id'], 'expected_version': run['profile_version'], 'plan_ids': [i['id'] for i in items], 'contact_ids': [contact], 'consent_ids': [consent['id']], 'demo_acknowledged': True}


def test_requests_are_verified_consented_owned_and_idempotent(fixture_client):
    client, _, engine = fixture_client
    seed_research(engine)
    headers, run = start(client)
    body = prepare_request(client, headers, run)
    a = client.post('/api/journey/quote-requests', headers=headers, json=body)
    assert a.status_code == 200, a.text
    b = client.post('/api/journey/quote-requests', headers=headers, json=body)
    assert a.json()['id'] == b.json()['id']
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Case)) == 1
        assert db.scalar(select(func.count()).select_from(QuoteRequest)) == len({i['plan']['insurer_id'] for i in run['items']})
    other, _ = start(client)
    assert client.get('/api/journey/cases/'+a.json()['id'], headers=other).status_code == 404
    client.delete('/api/journey/consents/'+body['consent_ids'][0], headers=headers)
    assert client.post('/api/journey/quote-requests', headers=headers, json=body).status_code == 422
