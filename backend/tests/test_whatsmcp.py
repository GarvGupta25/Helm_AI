import json
import re

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_wizard_verification import prepare

from app.config import settings
from app.journey import whatsmcp
from app.journey.case_models import Job
from app.journey.notifications import process_notifications


def setup_transport(monkeypatch,status=202,result=None):
    config=settings()
    for key,value in {'whatsmcp_api_key':'fake-server-key','whatsmcp_account_id':'test-account','otp_delivery_mode':'whatsmcp','otp_allowlist':['+12025550123'],'public_quote_origin':'https://helm.example.test','whatsapp_auth_template':'','whatsapp_utility_template':''}.items():
        monkeypatch.setattr(config,key,value)
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(status,json=result if result is not None else {'status':'queued'})
    constructor=httpx.Client
    monkeypatch.setattr(whatsmcp.httpx,'Client',lambda **kwargs:constructor(transport=httpx.MockTransport(handler),**kwargs))
    return calls


def test_real_transport_contract_queued_otp_link_consent_and_no_duplicate(fixture_client,monkeypatch):
    client,_,engine=fixture_client
    headers=prepare(client,engine,monkeypatch)
    calls=setup_transport(monkeypatch)
    start=client.post('/api/journey/verify/start',headers=headers,json={'channel':'whatsapp','country_code':'+1','number':'+12025550123','consent':True})
    assert start.status_code==200,start.text
    assert start.json()['delivery_status']=='queued'
    assert client.get('/api/journey/verify/demo-code',headers=headers).status_code==404
    payload=json.loads(calls[0].content)
    code=re.search(r'\b\d{6}\b',payload['text']).group()
    assert payload['to']=='12025550123' and calls[0].headers['x-api-key']=='fake-server-key'
    assert str(calls[0].url)=='https://api.whatsmcp.com/v1/accounts/test-account/messages'
    assert client.post('/api/journey/verify/check',headers=headers,json={'code':code}).json()['real_ownership_verified']
    access=client.post('/api/journey/wizard/access',headers=headers,json={'hours':24,'notifications':True})
    assert access.status_code==200,access.text
    with Session(engine) as db:
        process_notifications(db)
        job=db.scalar(select(Job).where(Job.kind=='access_link_notify'))
        assert job.status=='accepted' and job.data['provider_status']=='queued'
        assert process_notifications(db)==0
    assert len(calls)==2
    assert 'https://helm.example.test/my-quotes#' in json.loads(calls[1].content)['text']
    assert client.get('/api/journey/wizard/access',headers=headers).json()['delivery_status']=='accepted'
    assert client.post('/api/journey/wizard/access',headers=headers,json={'hours':24,'notifications':True}).json()['reused']
    assert len(calls)==2


@pytest.mark.parametrize(('status','result','expected'),[(401,{},503),(403,{},503),(409,{},503),(429,{},429),(500,{},503),(200,{'status':'refused'},503)])
def test_provider_failure_is_safe_and_does_not_fallback_to_fake_success(monkeypatch,status,result,expected):
    setup_transport(monkeypatch,status,result)
    with pytest.raises(whatsmcp.WhatsMCPError) as error:
        whatsmcp.send_message('+12025550123','Test message')
    assert error.value.status_code==expected
    assert 'fake-server-key' not in str(error.value)


def test_allowlist_public_origin_templates_and_timeout(monkeypatch):
    calls=setup_transport(monkeypatch,200,{'status':'sent'})
    with pytest.raises(whatsmcp.WhatsMCPError):
        whatsmcp.send_message('+12025550124','Do not send')
    assert not calls
    monkeypatch.setattr(settings(),'whatsapp_auth_template','approved_otp')
    assert whatsmcp.WhatsMCPOtpProvider().send('+12025550123','123456','local-reference')['provider_status']=='sent'
    assert json.loads(calls[0].content)=={'to':'12025550123','template':'approved_otp','template_language':'en','template_variables':['123456']}
    from types import SimpleNamespace
    contact=SimpleNamespace(data={'destination':'+12025550123'})
    monkeypatch.setattr(settings(),'public_quote_origin','http://127.0.0.1:4174')
    with pytest.raises(whatsmcp.WhatsMCPError):
        whatsmcp.WhatsMCPNotification().send(contact,'/my-quotes#'+'a'*43)
    assert len(calls)==1
    def timeout(**kwargs):
        raise httpx.ReadTimeout('Sensitive provider details must not escape')
    monkeypatch.setattr(whatsmcp.httpx,'Client',timeout)
    with pytest.raises(whatsmcp.WhatsMCPError,match='could not be confirmed'):
        whatsmcp.send_message('+12025550123','Do not retry automatically')
