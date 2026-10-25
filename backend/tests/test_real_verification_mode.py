from sqlalchemy import select
from sqlalchemy.orm import Session
from test_wizard_verification import prepare, request_code

from app.config import settings
from app.journey.case_models import Contact


def test_public_readiness_does_not_advertise_missing_credentials(fixture_client,monkeypatch):
    client,_,_=fixture_client
    config=settings()
    for key,value in {'otp_delivery_mode':'whatsmcp','whatsmcp_api_key':'','whatsmcp_account_id':'','otp_allowlist':[],'smtp_host':''}.items():
        monkeypatch.setattr(config,key,value)
    data=client.get('/api/journey/verify/config').json()
    assert not data['real_delivery'] and data['channels']=={'whatsapp':False,'email':False}
    monkeypatch.setattr(config,'whatsmcp_api_key','fixture-private-key')
    monkeypatch.setattr(config,'whatsmcp_account_id','fixture-account')
    assert not client.get('/api/journey/verify/config').json()['channels']['whatsapp']
    monkeypatch.setattr(config,'otp_allowlist',['+12025550123'])
    response=client.get('/api/journey/verify/config')
    assert response.json()['channels']['whatsapp'] and response.json()['real_delivery']
    assert 'fixture-private-key' not in response.text and '+12025550123' not in response.text


def test_console_challenge_cannot_be_used_after_real_mode_switch(fixture_client,monkeypatch):
    client,_,engine=fixture_client
    headers=prepare(client,engine,monkeypatch)
    assert request_code(client,headers).status_code==200
    code=client.get('/api/journey/verify/demo-code',headers=headers).json()['code']
    monkeypatch.setattr(settings(),'otp_delivery_mode','whatsmcp')
    assert client.get('/api/journey/verify/status',headers=headers).status_code==409
    assert client.get('/api/journey/verify/demo-code',headers=headers).status_code==404
    assert client.post('/api/journey/verify/check',headers=headers,json={'code':code}).status_code==409
    with Session(engine) as db:
        assert not db.scalar(select(Contact)).verified_at
