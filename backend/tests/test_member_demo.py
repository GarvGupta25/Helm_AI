from datetime import timedelta
from types import SimpleNamespace

from cryptography.fernet import Fernet
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app import member_demo
from app.auth import current_user
from app.main import app
from app.member_demo import DEMO_PASSWORD, MemberAccount, MemberSession, seed_demo_members
from app.models import now
from app.public_assistant import _rate_store


def test_accounts_password_sessions_policy_landing_and_broker_separation(fixture_client, monkeypatch):
    client, _, engine = fixture_client
    _rate_store.clear()
    monkeypatch.setenv('RESEARCH_STATE_KEY', Fernet.generate_key().decode())
    monkeypatch.setattr(member_demo, 'settings', lambda: SimpleNamespace(member_demo_auth=True, app_env='development'))
    with Session(engine) as db:
        assert seed_demo_members(db) == 2
        assert seed_demo_members(db) == 0
    assert client.get('/api/member-demo/me').status_code == 401
    body = {'name': 'Fictional Visitor', 'email': 'Fresh@Example.test', 'password': 'a strong demo password'}
    response = client.post('/api/member-demo/register', json=body)
    assert response.status_code == 200, response.text
    assert 'HttpOnly' in response.headers['set-cookie'] and 'SameSite=strict' in response.headers['set-cookie']
    result = client.get('/api/member-demo/me').json()
    assert result['name'] == body['name'] and result['email'] == body['email'].lower()
    assert result['has_policies'] is False and result['policies'] == []
    with Session(engine) as db:
        account = db.scalar(select(MemberAccount).where(MemberAccount.email_hash == member_demo.keyed('member:'+body['email'].lower())))
        assert account.password_hash != body['password']
        assert body['password'] not in str(db.execute(text('select password_hash, data from member_demo_account')).all())
    assert client.post('/api/member-demo/logout', json={}).status_code == 200
    assert client.get('/api/member-demo/me').status_code == 401
    assert client.post('/api/member-demo/login', json={'email': body['email'], 'password': 'incorrect'}).status_code == 401
    assert client.post('/api/member-demo/login', json={'email': body['email'].lower(), 'password': body['password']}).status_code == 200
    assert client.post('/api/member-demo/register', json=body).status_code == 409
    assert client.post('/api/member-demo/login', headers={'Origin': 'https://foreign.test'}, json={'email': body['email'], 'password': body['password']}).status_code == 403
    client.post('/api/member-demo/login', json={'email': 'policy.member@example.test', 'password': DEMO_PASSWORD})
    policyholder = client.get('/api/member-demo/me').json()
    assert policyholder['has_policies'] and len(policyholder['policies']) == 1
    assert policyholder['policies'][0]['currency'] == 'GBP'
    # A local member cookie is never a professional Supabase identity.
    app.dependency_overrides.pop(current_user)
    assert client.get('/api/journey/broker/me').status_code in {401, 503}
    with Session(engine) as db:
        for grant in db.scalars(select(MemberSession)):
            grant.expires_at = now()-timedelta(seconds=1)
        db.commit()
    assert client.get('/api/member-demo/me').status_code == 401
    for environment in ['production', 'prod', 'staging']:
        monkeypatch.setattr(member_demo, 'settings', lambda: SimpleNamespace(member_demo_auth=True, app_env=environment))
        assert client.post('/api/member-demo/login', json={'email': body['email'], 'password': body['password']}).status_code == 404
