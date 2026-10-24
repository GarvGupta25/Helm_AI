from datetime import timedelta
from uuid import uuid4

from sqlalchemy.orm import Session
from test_journey_access import link_token
from test_journey_compare_api import start
from test_journey_requests import prepare_request
from test_journey_review import exact, ready
from test_research_api import seed_research

from app.auth import User
from app.journey.case_models import Case
from app.journey.worker import process_quotes
from app.models import now


def test_two_visitors_and_two_brokers_complete_private_signoff_without_email_merging(fixture_client):
    client, owner, engine = fixture_client
    seed_research(engine)
    journeys = []
    for _ in range(2):
        client.cookies.clear()
        headers, run = start(client)
        body = prepare_request(client, headers, run)
        consent = client.post('/api/journey/consents', headers=headers, json={'purpose': 'broker_share', 'recipients': ['helm-demo-broker'], 'accepted': True, 'wording_version': 'journey-sharing-v1'}).json()
        body['consent_ids'].append(consent['id'])
        case = client.post('/api/journey/quote-requests', headers=headers, json=body).json()
        broker = User(str(uuid4()), 'broker@example.test', 'broker')
        with Session(engine) as db:
            row = db.get(Case, case['id'])
            row.broker_id = broker.id
            db.commit()
        token = link_token(client, headers, case)
        assert client.post('/api/journey/access-links/exchange', json={'token': token}).status_code == 200
        journeys.append({'headers': headers, 'body': body, 'case': case, 'broker': broker, 'cookie': client.cookies['helm_dashboard']})
    assert journeys[0]['case']['id'] != journeys[1]['case']['id']
    with Session(engine) as db:
        assert process_quotes(db, clock=now()+timedelta(seconds=5)) == 6
    for index, journey in enumerate(journeys):
        owner[0] = journey['broker']
        foreign = journeys[1-index]['case']['id']
        assert client.get('/api/journey/broker/cases').json()['total'] == 1
        for action, payload in [('notes', {'text': 'private'}), ('messages', {'text': 'private'}), ('transition', {'state': 'triaged'}), ('documents', {'kind': 'case_summary', 'audience': 'customer', 'recipients': journey['body']['contact_ids']})]:
            assert client.post(f'/api/journey/broker/cases/{foreign}/{action}', json={'expected_version': 1, **payload}).status_code == 404
        path = '/api/journey/broker/cases/'+journey['case']['id']
        data = client.get(path).json()
        for state in ['triaged', 'in_progress']:
            data = client.post(path+'/transition', json={'expected_version': data['version'], 'state': state}).json()
        data = client.post(path+'/documents', json={'expected_version': data['version'], 'kind': 'case_summary', 'audience': 'customer', 'recipients': journey['body']['contact_ids']}).json()
        data = ready(client, path, data)
        ident, payload = exact(data)
        docpath = path+'/documents/'+ident
        data = client.post(docpath+'/review', json={**payload, 'decision': 'approve'}).json()
        _, payload = exact(data)
        response = client.post(docpath+'/dispatch', json=payload)
        assert response.status_code == 200, response.text
        assert response.json()['state'] == 'submitted'
        client.cookies.clear()
        client.cookies.set('helm_dashboard', journey['cookie'], path='/api/journey')
        dashboard = client.get('/api/journey/dashboard').json()
        assert dashboard['id'] == journey['case']['id'] and len(dashboard['quotations']) == 3
        assert len(dashboard['messages']) == 1 and foreign not in dashboard['messages'][0]['text']
        journey['quotation_id'] = dashboard['quotations'][0]['id']
    client.cookies.clear()
    client.cookies.set('helm_dashboard', journeys[0]['cookie'], path='/api/journey')
    assert client.get('/api/journey/quotations/'+journeys[1]['quotation_id']+'/document').status_code == 404
    # Withdrawing one guest's health processing cannot erase the other guest's case.
    assert client.post('/api/journey/health-consent', headers=journeys[0]['headers'], json={'accepted': False}).status_code == 200
    owner[0] = journeys[1]['broker']
    assert client.get('/api/journey/broker/cases').json()['total'] == 1
    with Session(engine) as db:
        assert db.get(Case, journeys[1]['case']['id'])
        assert not db.get(Case, journeys[0]['case']['id'])
