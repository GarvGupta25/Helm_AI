from copy import deepcopy
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session
from test_journey_broker import broker_case

from app.journey.case_models import Approval, Case, Job
from app.journey.worker import process_quotes
from app.models import now


def ready(client, path, data):
    response = client.post(path+'/transition', json={'expected_version': data['version'], 'state': 'ready_for_signoff',
        'checklist': {'profile': True, 'quotations': True, 'questions': True, 'documents': True}})
    assert response.status_code == 200, response.text
    return response.json()


def document_case(fixture_client):
    client, owner, engine = fixture_client
    headers, body, case, consent = broker_case(client, owner, engine)
    with Session(engine) as db:
        process_quotes(db, clock=now()+timedelta(seconds=5))
    path = '/api/journey/broker/cases/'+case['id']
    data = client.get(path).json()
    for state in ['triaged', 'in_progress']:
        data = client.post(path+'/transition', json={'expected_version': data['version'], 'state': state}).json()
    response = client.post(path+'/documents', json={'expected_version': data['version'], 'kind': 'case_summary', 'audience': 'customer', 'recipients': body['contact_ids']})
    assert response.status_code == 200, response.text
    return client, engine, headers, consent, path, response.json()


def exact(data):
    doc = next(d for d in data['documents'] if d['ai_drafted'])
    return doc['id'], {'expected_version': data['version'], 'revision': doc['revision'], 'content_hash': doc['hash']}


def test_exact_approval_edit_invalidation_and_simulated_dispatch(fixture_client):
    client, engine, _, _, path, data = document_case(fixture_client)
    data = ready(client, path, data)
    ident, body = exact(data)
    docpath = path+'/documents/'+ident
    assert client.post(docpath+'/dispatch', json=body).status_code == 403
    data = client.post(docpath+'/review', json={**body, 'decision': 'approve'}).json()
    _, body = exact(data)
    data = client.post(docpath+'/edit', json={**body, 'text': 'Human edited this exact draft. Synthetic general information only.'}).json()
    with Session(engine) as db:
        assert all(a.revoked for a in db.scalars(select(Approval)))
        assert db.scalars(select(Job).where(Job.kind == 'approved_dispatch')).all() == []
    assert data['state'] == 'in_progress'
    data = ready(client, path, data)
    _, revised = exact(data)
    assert client.post(docpath+'/review', json={**body, 'expected_version': data['version'], 'decision': 'approve'}).status_code == 409
    assert client.post(docpath+'/dispatch', json=revised).status_code == 403
    data = client.post(docpath+'/review', json={**revised, 'decision': 'approve'}).json()
    _, body = exact(data)
    response = client.post(docpath+'/dispatch', json=body)
    assert response.status_code == 200, response.text
    assert response.json()['state'] == 'submitted'
    assert client.post(docpath+'/dispatch', json=body).status_code == 409
    with Session(engine) as db:
        jobs = db.scalars(select(Job).where(Job.kind == 'approved_dispatch')).all()
        assert len(jobs) == 1 and jobs[0].data['external_sent'] is False
        assert jobs[0].data['revision'] == 2


def test_withdrawal_after_approval_blocks_dispatch(fixture_client):
    client, engine, headers, consent, path, data = document_case(fixture_client)
    data = ready(client, path, data)
    ident, body = exact(data)
    docpath = path+'/documents/'+ident
    data = client.post(docpath+'/review', json={**body, 'decision': 'approve'}).json()
    _, body = exact(data)
    assert client.delete('/api/journey/consents/'+consent['id'], headers=headers).status_code == 200
    assert client.post(docpath+'/dispatch', json=body).status_code == 404
    with Session(engine) as db:
        assert not db.scalars(select(Job).where(Job.kind == 'approved_dispatch')).all()


def test_recipient_or_profile_change_invalidates_approval(fixture_client):
    client, engine, _, _, path, data = document_case(fixture_client)
    data = ready(client, path, data)
    ident, body = exact(data)
    docpath = path+'/documents/'+ident
    data = client.post(docpath+'/review', json={**body, 'decision': 'approve'}).json()
    with Session(engine) as db:
        case = db.get(Case, data['id'])
        copy = deepcopy(case.data)
        copy['profile_version'] += 1
        case.data = copy
        db.commit()
    data = client.get(path).json()
    _, body = exact(data)
    assert client.post(docpath+'/dispatch', json=body).status_code == 409
