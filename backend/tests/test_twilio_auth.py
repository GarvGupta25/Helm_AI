"""No real provider calls: exercise the same reviewed-selection HTTP flow."""
import json
from datetime import timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_wizard_verification import prepare
from twilio.request_validator import RequestValidator

from app.config import settings
from app.journey import twilio_auth
from app.journey.case_models import Contact, Grant, Job, OtpWindow
from app.models import now

PHONE = '+919876543210'


def configure(monkeypatch, mode='twilio', otp='twilio_verify'):
    fields = {'otp_delivery_mode': mode, 'app_env': 'test', 'whatsapp_mock_auth': True,
              'otp_allowlist': [PHONE], 'twilio_account_sid': 'AC'+'a'*32, 'twilio_auth_token': 'fixture-secret',
              'twilio_verify_service_sid': 'VA'+'b'*32, 'twilio_whatsapp_from': 'whatsapp:+14155238886',
              'public_quote_origin': 'https://helm.example.test', 'twilio_webhook_origin': 'https://hooks.example.test',
              'twilio_otp_provider': otp, 'twilio_otp_content_sid': 'HX'+'c'*32,
              'twilio_magic_link_content_sid': '', 'twilio_sandbox': True,
              'twilio_legacy_session_messages': False, 'magic_link_expiry_minutes': 10}
    for field, value in fields.items():
        monkeypatch.setattr(settings(), field, value)


class FakeTwilio:
    def __init__(self):
        self.calls = []
        self.fail = False
        self.verifications = SimpleNamespace(create=self.start)
        self.verification_checks = SimpleNamespace(create=self.check)
        self.verify = SimpleNamespace(v2=SimpleNamespace(services=lambda sid: self))
        self.messages = self

    def start(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail:
            raise RuntimeError('private-provider-details')
        return SimpleNamespace(status='pending', sid='VE'+'d'*32)

    def check(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail:
            raise RuntimeError('private-provider-details')
        return SimpleNamespace(status='approved' if kwargs['code']=='765432' else 'pending', to=PHONE)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail:
            raise RuntimeError('private-provider-details')
        return SimpleNamespace(status='queued', sid='SM'+'e'*32)

    def __call__(self, sid):
        return SimpleNamespace(fetch=lambda: SimpleNamespace(direction='inbound', from_='whatsapp:'+PHONE,
                                  to=settings().twilio_whatsapp_from, date_created=now()))


def begin(client, headers, number=PHONE):
    return client.post('/api/journey/verify/start', headers=headers,
                       json={'number': number, 'country_code': '+91', 'consent': True})


def test_managed_otp_blocked_trial_has_no_token_leak_and_no_custom_fallback(fixture_client, monkeypatch):
    client, _, engine = fixture_client
    headers = prepare(client, engine, monkeypatch)
    configure(monkeypatch)
    fake = FakeTwilio()
    monkeypatch.setattr(twilio_auth, 'client', lambda: fake)
    assert client.post('/api/journey/verify/magic-link', headers=headers, json={}).status_code == 404
    assert begin(client, headers, 'invalid').status_code == 422
    assert begin(client, headers).status_code == 200
    assert client.get('/api/journey/verify/demo-code', headers=headers).status_code == 404
    assert client.post('/api/journey/verify/magic-link', headers=headers, json={}).status_code == 403
    assert client.post('/api/journey/verify/check', headers=headers, json={'code':'111111'}).status_code == 422
    result = client.post('/api/journey/verify/check', headers=headers, json={'code':'765432'})
    assert result.status_code == 200, result.text
    assert result.json()['real_ownership_verified']
    assert result.json()['magic_link']['delivery_status'] == 'blocked'
    assert 'url' not in result.text and '#'+('x'*43) not in result.text
    assert client.post('/api/journey/verify/check', headers=headers, json={'code':'765432'}).status_code == 410
    assert client.get('/api/journey/verify/mock-link', headers=headers).status_code == 404
    with Session(engine) as db:
        contact = db.scalar(select(Contact))
        assert contact.data['challenge_hash'] == '' and contact.data['attempts'] == 2
        grant = db.scalar(select(Grant).where(Grant.kind=='magic_link'))
        assert 590 < (grant.expires_at.replace(tzinfo=timezone.utc)-now()).total_seconds() <= 600
        assert all('url' not in j.data for j in db.scalars(select(Job)))
    # Idempotent request does not send a second message, invent a new token, or leak the first.
    assert client.post('/api/journey/verify/magic-link', headers=headers, json={}).json()['delivery_status']=='blocked'
    assert 'url' not in client.get('/api/journey/wizard/access', headers=headers).json()
    assert client.get('/api/journey/demo/inbox', headers=headers).json() == []
    assert not any('content_sid' in c for c in fake.calls)


def test_mock_flow_proves_expiry_single_use_session_cookie_and_isolation(fixture_client, monkeypatch):
    client, _, engine = fixture_client
    headers = prepare(client, engine, monkeypatch)
    configure(monkeypatch, 'mock')
    assert client.get('/api/journey/verify/config').json()['mock']
    assert begin(client, headers).status_code == 200
    assert client.post('/api/journey/verify/resend', headers=headers, json={}).status_code == 429
    code = client.get('/api/journey/verify/demo-code', headers=headers).json()['code']
    verified = client.post('/api/journey/verify/check', headers=headers, json={'code':code})
    assert verified.status_code == 200, verified.text
    assert not verified.json()['real_ownership_verified']
    assert client.get('/api/journey/verify/mock-link').status_code == 404
    url = client.get('/api/journey/verify/mock-link', headers=headers).json()['url']
    token = url.split('#')[1]
    assert client.get('/my-quotes').status_code != 200  # Backend GET never consumes a token.
    assert client.post('/api/journey/access-links/exchange', headers={'Origin':'https://evil.test'}, json={'token':token}).status_code==403
    redeemed = client.post('/api/journey/access-links/exchange', json={'token':token})
    assert redeemed.status_code == 200
    assert 'HttpOnly' in redeemed.headers['set-cookie'] and 'SameSite=strict' in redeemed.headers['set-cookie']
    assert client.post('/api/journey/access-links/exchange', json={'token':token}).status_code==410
    assert client.get('/api/journey/dashboard').status_code==200
    assert client.get('/api/journey/verify/mock-link', headers=headers).status_code==410
    monkeypatch.setattr(settings(), 'app_env', 'production')
    with pytest.raises(RuntimeError):
        twilio_auth.validate_startup()
    assert client.get('/api/journey/verify/mock-link', headers=headers).status_code==404


@pytest.mark.parametrize('mode', ['custom', 'twilio_verify'])
def test_provider_failure_and_attempt_limits(fixture_client, monkeypatch, mode):
    client, _, engine = fixture_client
    headers = prepare(client, engine, monkeypatch)
    configure(monkeypatch, otp=mode)
    fake = FakeTwilio()
    monkeypatch.setattr(twilio_auth, 'client', lambda: fake)
    fake.fail = True
    result = begin(client, headers)
    assert result.status_code==503 and 'private-provider-details' not in result.text
    assert client.post('/api/journey/verify/check', headers=headers, json={'code':'765432'}).status_code in {404,410}
    with Session(engine) as db:
        for row in db.scalars(select(OtpWindow)):
            row.data={'sends':[]}
        db.commit()
    fake.fail = False
    assert begin(client, headers).status_code==200
    for _ in range(5):
        assert client.post('/api/journey/verify/check', headers=headers, json={'code':'111111'}).status_code==422
    assert client.post('/api/journey/verify/check', headers=headers, json={'code':'765432'}).status_code==429
    with Session(engine) as db:
        assert db.scalar(select(Grant).where(Grant.kind=='magic_link')) is None


def signed(client, path, data, valid=True):
    url = twilio_auth.callback(path)
    signature = RequestValidator(settings().twilio_auth_token).compute_signature(url, data)
    return client.post('/api/journey/webhooks/twilio/'+path, data=data,
                       headers={'X-Twilio-Signature':signature if valid else 'invalid'})


def test_custom_sandbox_otp_inbound_window_magic_link_and_status(fixture_client, monkeypatch):
    client, _, engine = fixture_client
    headers = prepare(client, engine, monkeypatch)
    configure(monkeypatch, otp='custom')
    fake = FakeTwilio()
    monkeypatch.setattr(twilio_auth, 'client', lambda: fake)
    monkeypatch.setattr(settings(), 'twilio_legacy_session_messages', True)
    data={'AccountSid':settings().twilio_account_sid, 'MessageSid':'SM'+'e'*32,
          'From':'whatsapp:'+PHONE, 'To':settings().twilio_whatsapp_from}
    assert signed(client,'inbound',data,False).status_code==403
    assert signed(client,'inbound',data).status_code==204
    assert begin(client, headers).status_code==200
    args = fake.calls[-1]
    assert args['content_sid']==settings().twilio_otp_content_sid and 'body' not in args
    code=json.loads(args['content_variables'])['2']
    result=client.post('/api/journey/verify/check', headers=headers, json={'code':code})
    assert result.status_code==200 and result.json()['magic_link']['delivery_status']=='accepted'
    message=fake.calls[-1]
    assert message['to']=='whatsapp:'+PHONE and '/my-quotes#' in message['body']
    token=message['body'].split('/my-quotes#')[1].split(' ')[0]
    assert token not in result.text
    with Session(engine) as db:
        assert all(token not in json.dumps(j.data) for j in db.scalars(select(Job)))
    status={'AccountSid':settings().twilio_account_sid,'MessageSid':'SM'+'e'*32,'MessageStatus':'delivered'}
    assert signed(client,'status',status,False).status_code==403
    assert signed(client,'status',status).status_code==204
    assert signed(client,'status',status).status_code==204
    status['MessageStatus']='queued'
    assert signed(client,'status',status).status_code==204
    assert client.get('/api/journey/verify/magic-link',headers=headers).json()['delivery_status']=='delivered'
    assert client.post('/api/journey/access-links/exchange',json={'token':token}).status_code==200


def test_production_templates_and_missing_credentials(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setattr(settings(),'twilio_auth_token','')
    assert not twilio_auth.ready()
    with pytest.raises(RuntimeError):
        twilio_auth.validate_startup()
    configure(monkeypatch)
    monkeypatch.setattr(settings(),'app_env','production')
    assert not twilio_auth.ready()
    monkeypatch.setattr(settings(),'twilio_sandbox',False)
    monkeypatch.setattr(settings(),'twilio_magic_link_content_sid','HX'+'f'*32)
    assert twilio_auth.ready()
    fake=FakeTwilio()
    monkeypatch.setattr(twilio_auth,'client',lambda:fake)
    contact=SimpleNamespace(verified_at=now(),data={'mode':'twilio','destination':PHONE})
    delivery=twilio_auth.send_link(None,contact,'/my-quotes#'+'x'*43)
    assert delivery['provider_status']=='accepted'
    assert fake.calls[-1]['content_sid']=='HX'+'f'*32 and 'body' not in fake.calls[-1]
    assert json.loads(fake.calls[-1]['content_variables'])['1'].startswith('https://helm.example.test/my-quotes#')


@pytest.mark.parametrize('otp', ['custom', 'twilio_verify'])
def test_expired_attempt_and_provider_switch_never_authenticate(fixture_client, monkeypatch, otp):
    client, _, engine=fixture_client
    headers=prepare(client,engine,monkeypatch)
    configure(monkeypatch,otp=otp)
    monkeypatch.setattr(twilio_auth,'client',lambda:FakeTwilio())
    assert begin(client,headers).status_code==200
    with Session(engine) as db:
        contact=db.scalar(select(Contact))
        contact.data={**contact.data,'expires_at':(now()-timedelta(seconds=1)).isoformat()}
        db.commit()
    assert client.post('/api/journey/verify/check',headers=headers,json={'code':'765432'}).status_code==410
    monkeypatch.setattr(settings(),'twilio_otp_provider','custom' if otp=='twilio_verify' else 'twilio_verify')
    assert client.post('/api/journey/verify/check',headers=headers,json={'code':'765432'}).status_code==409
    with Session(engine) as db:
        assert db.scalar(select(Grant).where(Grant.kind=='magic_link')) is None


def test_two_concurrent_redemptions_have_exactly_one_winner(fixture_client, monkeypatch, tmp_path):
    import sqlite3
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from fastapi import HTTPException, Response
    from sqlalchemy import create_engine
    from starlette.requests import Request

    from app.journey import access

    client, _, engine=fixture_client
    headers=prepare(client,engine,monkeypatch)
    configure(monkeypatch,'mock')
    assert begin(client,headers).status_code==200
    code=client.get('/api/journey/verify/demo-code',headers=headers).json()['code']
    assert client.post('/api/journey/verify/check',headers=headers,json={'code':code}).status_code==200
    token=client.get('/api/journey/verify/mock-link',headers=headers).json()['url'].split('#')[1]
    database=tmp_path/'race.db'
    with engine.connect() as connection, sqlite3.connect(database) as target:
        connection.connection.driver_connection.backup(target)
    concurrent=create_engine('sqlite:///'+database.as_posix(),connect_args={'check_same_thread':False})
    barrier=Barrier(2)
    original=access.valid_grant

    def synchronized(db, value, kind):
        result=original(db,value,kind)
        barrier.wait(timeout=10)
        return result

    monkeypatch.setattr(access,'valid_grant',synchronized)

    def redeem(_):
        request=Request({'type':'http','method':'POST','scheme':'https','path':'/api/journey/access-links/exchange',
                         'server':('helm.example.test',443),'headers':[], 'client':('127.0.0.1',1234)})
        with Session(concurrent) as db:
            try:
                access.exchange(access.Exchange(token=token),request,Response(),db)
                return 200
            except HTTPException as exc:
                return exc.status_code
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(redeem,range(2)))==[200,410]
        with Session(concurrent) as db:
            assert len(db.scalars(select(Grant).where(Grant.kind=='dashboard_session')).all())==1
    finally:
        concurrent.dispose()
