from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.journey.funnel import FunnelCount, purge_counts
from app.models import now
from app.public_assistant import _rate_store


def test_counts_disabled_consent_origin_schema_and_aggregate_retention(fixture_client,monkeypatch):
    client,_,engine=fixture_client
    settings().journey_funnel_enabled=False
    body={'event':'step_view','step':'people','mode':'manual','choice':'','analytics_consent':True}
    assert client.post('/api/journey/funnel',json=body).status_code==204
    with Session(engine) as db:
        assert db.scalars(select(FunnelCount)).all()==[]
    monkeypatch.setattr(settings(),'journey_funnel_enabled',True)
    _rate_store.clear()
    assert client.post('/api/journey/funnel',json={**body,'email':'private@example.test'}).status_code==422
    assert client.post('/api/journey/funnel',json={**body,'step':'private-answer'}).status_code==422
    assert client.post('/api/journey/funnel',json={**body,'analytics_consent':False}).status_code==422
    assert client.post('/api/journey/funnel',json=body,headers={'Origin':'https://untrusted.invalid'}).status_code==403
    for _ in range(10):
        assert client.post('/api/journey/funnel',json=body).status_code==204
    assert client.post('/api/journey/funnel',json=body).status_code==429
    with Session(engine) as db:
        row=db.scalar(select(FunnelCount))
        assert row.count==10
        assert set(FunnelCount.__table__.columns.keys())=={'key','day','event','step','mode','choice','count'}
        purge_counts(db,now()+timedelta(days=32))
        db.commit()
        assert db.scalars(select(FunnelCount)).all()==[]
