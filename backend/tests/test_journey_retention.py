from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_journey_access import link_token, make_case

from app.journey.case_models import Case, Contact, Document, Grant, Job, Quotation
from app.journey.models import JourneyRun, JourneySession, ProfileVersion
from app.journey.retention import purge_expired
from app.journey.schemas import JourneyProfile, completeness
from app.journey.worker import process_quotes
from app.models import now


def test_sensitive_withdrawal_erases_derived_runs_and_cases(fixture_client):
    client, _, engine = fixture_client
    headers, _, case = make_case(client, engine)
    with Session(engine) as db:
        process_quotes(db, clock=now()+timedelta(seconds=5))
    token = link_token(client, headers, case)
    assert client.post('/api/journey/access-links/exchange', json={'token': token}).status_code == 200
    response = client.post('/api/journey/health-consent', headers=headers, json={'accepted': False})
    assert response.status_code == 200, response.text
    assert response.json()['latest_run'] is None
    assert client.get('/api/journey/dashboard').status_code == 410
    with Session(engine) as db:
        for model in (JourneyRun, ProfileVersion, Case, Document, Quotation):
            assert db.scalar(select(func.count()).select_from(model)) == 0
        assert not db.scalars(select(Job).where(Job.case_id.is_not(None))).all()


def test_intake_and_independent_case_retention(fixture_client):
    client, _, engine = fixture_client
    headers, _, case = make_case(client, engine)
    token = link_token(client, headers, case)
    client.post('/api/journey/access-links/exchange', json={'token': token})
    with Session(engine) as db:
        process_quotes(db, clock=now()+timedelta(seconds=5))
        assert purge_expired(db, clock=now()+timedelta(hours=25)) == 0
        assert db.scalar(select(JourneySession)).data == {'purged': True}
        assert db.get(Case, case['id']).data['profile']
        assert purge_expired(db, clock=now()+timedelta(days=8)) == 1
        for model in (Case, Contact, Document, Quotation, Grant, Job):
            assert db.scalar(select(func.count()).select_from(model)) == 0


def test_overnight_start_date_remains_readable_but_incomplete():
    profile = JourneyProfile.model_validate({'cover': {'start_date': (date.today()-timedelta(days=1)).isoformat()}})
    assert 'cover' in {m['field'] for m in completeness(profile, strict=False)['missing']}
