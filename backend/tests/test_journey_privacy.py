from sqlalchemy import select
from sqlalchemy.orm import Session
from test_journey_review import document_case

from app.journey.case_models import Case, Contact, Grant, Job
from app.journey.models import JourneyRun, JourneySession, ProfileVersion


def test_export_redacts_secrets_delete_cascades_and_isolates(fixture_client):
    client,engine,headers,_,_,_=document_case(fixture_client)
    other=client.post('/api/journey/sessions').json()
    response=client.get('/api/journey/privacy/export',headers=headers)
    assert response.status_code==200 and response.json()['contacts'][0]['destination']=='request@example.test'
    assert all(secret not in response.text for secret in ['challenge_hash','token_hash','session_token','lookup_hash','code_hmac'])
    assert client.get('/api/journey/privacy/export').status_code==404
    assert client.post('/api/journey/privacy/delete',headers={**headers,'Origin':'https://bad.invalid'},json={'confirm':True}).status_code==403
    assert client.post('/api/journey/privacy/delete',headers=headers,json={'confirm':False}).status_code==422
    assert client.post('/api/journey/privacy/delete',headers=headers,json={'confirm':True}).json()['deleted']
    assert client.get('/api/journey/profile',headers=headers).status_code==404
    assert client.get('/api/journey/profile',headers={'X-Journey-Session':other['session_token']}).status_code==200
    with Session(engine) as db:
        for model in (Case,Contact,Grant,Job,JourneyRun,ProfileVersion):
            assert db.scalars(select(model)).all()==[]
        assert len(db.scalars(select(JourneySession)).all())==1
