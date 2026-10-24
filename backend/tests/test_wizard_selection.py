import pytest
from test_journey_compare_api import start
from test_research_api import seed_research


@pytest.mark.parametrize('count',[1,2,3])
def test_consent_bound_multi_selection_is_idempotent_and_conflict_safe(fixture_client,count):
    client,_,engine=fixture_client
    seed_research(engine)
    headers,_=start(client)
    run=client.post('/api/journey/recommendations?limit=10',headers=headers).json()
    items=run['items'][:count]
    consent=client.post('/api/journey/consents',headers=headers,json={'purpose':'insurer_share','recipients':sorted({i['plan']['insurer_id'] for i in items}),'accepted':True,'wording_version':'journey-sharing-v1'}).json()
    body={'run_id':run['run_id'],'expected_version':1,'plan_ids':[i['id'] for i in items],'insurer_consent_id':consent['id']}
    first=client.post('/api/journey/selection',headers=headers,json=body)
    assert first.status_code==200
    assert client.post('/api/journey/selection',headers=headers,json=body).json()==first.json()
    assert first.json()['paid_pence']==0 and not first.json()['policy_created'] and not first.json()['account_linked']
    assert client.get('/api/journey/selection').status_code==404
    assert client.post('/api/journey/selection',headers=headers,json={**body,'expected_version':0}).status_code==409
    assert client.post('/api/journey/selection',headers=headers,json={**body,'plan_ids':[i['id'] for i in run['items'][:4]]}).status_code==422
    conflicting=client.post('/api/journey/selection',headers=headers,json={**body,'plan_ids':[i['id'] for i in run['items'][1:count+1]]})
    assert conflicting.status_code in {409,422}
    client.delete('/api/journey/consents/'+consent['id'],headers=headers)
    assert client.get('/api/journey/selection',headers=headers).status_code==422
