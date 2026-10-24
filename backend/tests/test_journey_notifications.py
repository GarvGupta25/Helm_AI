from copy import deepcopy
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
from test_journey_access import link_token, make_case

from app.journey.case_models import Case, Job
from app.journey.models import JourneySession
from app.journey.notifications import process_notifications, quiet_until
from app.models import now


def test_quiet_hours_wrap_midnight_and_dst():
    preferences = {'time_zone': 'Europe/London', 'quiet_start': 22, 'quiet_end': 8}
    assert quiet_until(preferences, datetime(2026, 10, 23, 22, tzinfo=timezone.utc)).hour == 7
    assert quiet_until(preferences, datetime(2026, 10, 24, 22, tzinfo=timezone.utc)).hour == 8
    assert quiet_until(preferences, datetime(2026, 10, 25, 1, tzinfo=timezone.utc)).hour == 8
    assert quiet_until(preferences, datetime(2026, 10, 25, 12, tzinfo=timezone.utc)) is None


def test_outbox_consent_dedupe_quiet_and_optout(fixture_client):
    client, _, engine = fixture_client
    headers, body, case = make_case(client, engine)
    token = link_token(client, headers, case)
    with Session(engine) as db:
        row = db.get(Case, case['id'])
        data = deepcopy(row.data)
        data['consents'].append({'id': 'notify', 'purpose': 'notify_email', 'recipients': body['contact_ids'], 'revoked': False})
        data['preferences']['channels'] = ['dashboard', 'email']
        data['preferences']['quiet_start'] = 0
        data['preferences']['quiet_end'] = 0
        row.data = data
        job = Job(case_id=row.id, contact_id=row.contact_id, kind='quote_update', dedupe_key='test-update', due_at=now(), data={'template': 'quote_ready_v1'})
        db.add(job)
        db.commit()
        assert process_notifications(db) == 1
        assert job.status == 'delivered_demo' and job.data['external_sent'] is False
        assert process_notifications(db) == 0
    assert client.post('/api/journey/access-links/exchange', json={'token': token}).status_code == 200
    assert client.post('/api/journey/dashboard/notifications/stop').status_code == 200
    with Session(engine) as db:
        assert all(j.status == 'cancelled' for j in db.scalars(select(Job).where(Job.kind == 'link_reminder')))


def test_recovery_after_intake_expiry_requires_protected_mailbox_and_code(fixture_client):
    client, _, engine = fixture_client
    headers, body, case = make_case(client, engine)
    with Session(engine) as db:
        row = db.get(Case, case['id'])
        db.get(JourneySession, row.session_id).expires_at = now()-timedelta(seconds=1)
        db.commit()
    result = client.post('/api/journey/access-links/recover', json={'case_id': case['id'], 'channel': 'email', 'destination': 'request@example.test'})
    assert result.status_code == 200
    contact_id = result.json()['contact_id']
    mails = client.get('/api/journey/demo/inbox', headers=headers)
    assert mails.status_code == 200
    code = next(j['content']['code'] for j in mails.json() if j['kind'] == 'verification' and j['content'].get('code'))
    payload = {'case_id': case['id'], 'contact_id': contact_id, 'code': code}
    assert client.post('/api/journey/access-links/recover/verify', json=payload).status_code == 200
    assert client.post('/api/journey/access-links/recover/verify', json=payload).status_code == 410
    client.cookies.clear()
    assert client.get('/api/journey/demo/inbox', headers=headers).status_code == 410
