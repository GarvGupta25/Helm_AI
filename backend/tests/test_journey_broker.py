from copy import deepcopy
from uuid import uuid4

from sqlalchemy.orm import Session
from test_journey_access import make_case

from app.auth import User
from app.journey.broker import TRANSITIONS
from app.journey.case_models import Case


def broker_case(client, owner, engine):
    headers, body, case = make_case(client, engine)
    broker = User(str(uuid4()), 'broker@example.test', 'broker')
    consent = client.post('/api/journey/consents', headers=headers, json={'purpose': 'broker_share', 'recipients': ['helm-demo-broker'], 'accepted': True, 'wording_version': 'journey-sharing-v1'}).json()
    with Session(engine) as db:
        row = db.get(Case, case['id'])
        row.data = {**deepcopy(row.data), 'consents': row.data['consents']+[consent]}
        row.broker_id = broker.id
        db.commit()
    owner[0] = broker
    return headers, body, case, consent


def test_broker_role_assignment_counts_and_revocation(fixture_client):
    client, owner, engine = fixture_client
    headers, _, case, consent = broker_case(client, owner, engine)
    path = '/api/journey/broker/cases/'+case['id']
    assert client.get('/api/journey/broker/cases').json()['total'] == 1
    detail = client.get(path).json()
    assert detail['contacts'][0]['destination'] == 'request@example.test'
    for role, status in [('member', 403), ('provider', 403), ('broker', 404)]:
        owner[0] = User(str(uuid4()), 'other@example.test', role)
        assert client.get(path).status_code == status
        assert client.post(path+'/notes', json={'expected_version': detail['version'], 'text': 'unauthorized'}).status_code == status
        if role == 'broker':
            assert client.get('/api/journey/broker/cases').json()['total'] == 0
    client.delete('/api/journey/consents/'+consent['id'], headers=headers)
    assert client.get(path).status_code == 404


def test_transitions_require_current_version_and_signoff_cannot_be_skipped(fixture_client):
    client, owner, engine = fixture_client
    _, _, case, _ = broker_case(client, owner, engine)
    path = '/api/journey/broker/cases/'+case['id']
    data = client.get(path).json()
    assert client.post(path+'/transition', json={'expected_version': data['version'], 'state': 'submitted'}).status_code == 422
    for state in ['triaged', 'in_progress', 'awaiting_customer', 'in_progress', 'awaiting_insurer', 'in_progress']:
        previous = data['version']
        response = client.post(path+'/transition', json={'expected_version': previous, 'state': state})
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['version'] > previous
        assert client.post(path+'/notes', json={'expected_version': previous, 'text': 'stale'}).status_code == 409
    assert client.post(path+'/transition', json={'expected_version': data['version'], 'state': 'ready_for_signoff'}).status_code == 422
    response = client.post(path+'/notes', json={'expected_version': data['version'], 'text': '<script>plain text only</script>'})
    data = response.json()
    assert client.post(path+'/transition', json={'expected_version': data['version'], 'state': 'closed'}).status_code == 422
    data = client.post(path+'/transition', json={'expected_version': data['version'], 'state': 'closed', 'reason': 'Demo completed'}).json()
    assert data['state'] == 'closed'
    assert len(data['audit']) == 9
    assert TRANSITIONS['closed'] == set()


def test_early_incomplete_handoff_is_consented_and_deduplicated(fixture_client):
    client, owner, engine = fixture_client
    headers, body, case = make_case(client, engine)
    consent = client.post('/api/journey/consents', headers=headers, json={'purpose': 'broker_share', 'recipients': ['helm-demo-broker'], 'accepted': True, 'wording_version': 'journey-sharing-v1'}).json()
    payload = {'contact_id': body['contact_ids'][0], 'consent_id': consent['id'], 'expected_version': case['profile_version'], 'demo_acknowledged': True}
    first = client.post('/api/journey/broker-handoff', headers=headers, json=payload)
    assert first.status_code == 200, first.text
    assert first.json()['broker_assigned'] is False
    assert client.post('/api/journey/broker-handoff', headers=headers, json=payload).json()['id'] == first.json()['id']
    assert client.get('/api/journey/broker/cases').status_code == 403
