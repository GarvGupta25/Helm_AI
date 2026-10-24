from uuid import uuid4

from sqlalchemy.orm import Session
from test_journey_access import make_case

from app.auth import User
from app.journey.case_models import Case


def test_broker_preferences_shortlist_summary_and_authority(fixture_client,monkeypatch):
    client,owner,engine=fixture_client
    headers,body,case=make_case(client,engine)
    run_id=client.get('/api/journey/profile',headers=headers).json()['latest_run']
    run=client.get('/api/journey/runs/'+run_id,headers=headers).json()
    ids=[run['items'][0]['id']]
    client.put('/api/journey/shortlist',headers=headers,json={'run_id':run_id,'expected_version':case['profile_version'],'plan_ids':ids})
    consent=client.post('/api/journey/consents',headers=headers,json={'purpose':'broker_share','recipients':['helm-demo-broker'],'accepted':True,'wording_version':'journey-sharing-v1'}).json()
    broker=User(str(uuid4()),'fixture-broker@example.test','broker')
    monkeypatch.setenv('JOURNEY_DEMO_BROKER_ID',broker.id)
    response=client.post('/api/journey/broker-handoff',headers=headers,json={'contact_id':body['contact_ids'][0],'consent_id':consent['id'],'expected_version':case['profile_version'],'demo_acknowledged':True,'preferred_channel':'callback','best_time':'Weekday afternoons','note':'Please explain the excess.'})
    assert response.status_code==200
    owner[0]=broker
    detail=client.get('/api/journey/broker/cases/'+response.json()['id']).json()
    assert detail['preferences']['preferred_channel']=='callback'
    assert detail['preferences']['best_time']=='Weekday afternoons'
    assert detail['selected'][0]['id']==ids[0]
    assert detail['summary']['hard_requirements']['benefits']==detail['profile']['benefits']
    with Session(engine) as db:
        row=db.get(Case,response.json()['id'])
        assert row.broker_id==broker.id and row.data['audit']
    client.delete('/api/journey/consents/'+consent['id'],headers=headers)
    assert client.get('/api/journey/broker/cases/'+response.json()['id']).status_code==404
