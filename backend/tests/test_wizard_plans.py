from copy import deepcopy

from test_journey_compare_api import start
from test_journey_recommendations import filled
from test_research_api import seed_research

from app.journey.compare import ViewFilters, filter_view
from app.journey.recommendations import compute
from app.research.generator import CONFIG, generate


def test_long_list_retains_diverse_top_three_and_view_filters():
    plans = generate({**CONFIG,'profiles':0,'histories':0})['variants']
    profile = filled()
    default = compute(plans,profile)
    extended = compute(plans,profile,limit=10)
    assert len(extended['items']) == 10
    assert extended['items'][:3] == default['items']
    assert len({i['id'] for i in extended['items']}) == 10
    snapshot = deepcopy(extended)
    view = filter_view(extended['items'],ViewFilters(excess_max=25000,sort='premium'))
    assert all(i['plan']['excess_pence']<=25000 for i in view)
    assert [i['quote']['monthly_pence'] for i in view] == sorted(i['quote']['monthly_pence'] for i in view)
    assert not filter_view(extended['items'],ViewFilters(benefits=['pre_existing']))
    assert extended == snapshot


def test_display_filter_api_does_not_mutate_profile_or_run(fixture_client):
    client,_,engine=fixture_client
    seed_research(engine)
    headers,_=start(client)
    run=client.post('/api/journey/recommendations?limit=10',headers=headers).json()
    before=client.get('/api/journey/profile',headers=headers).json()
    response=client.post(f"/api/journey/runs/{run['run_id']}/view",headers=headers,json={'budget_max':0})
    assert response.status_code==200 and response.json()['items']==[]
    assert client.get('/api/journey/profile',headers=headers).json()==before
    assert client.get(f"/api/journey/runs/{run['run_id']}",headers=headers).json()==run
    assert client.post('/api/journey/recommendations?limit=11',headers=headers).status_code==422
