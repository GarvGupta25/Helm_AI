import json
from datetime import timedelta

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from test_journey_compare_api import start
from test_research_api import seed_research

from app.config import settings
from app.journey.case_models import Contact, OtpWindow
from app.journey.verification import WhatsAppCloudProvider, destination
from app.models import now


def prepare(client,engine,monkeypatch):
    monkeypatch.setenv('RESEARCH_STATE_KEY',Fernet.generate_key().decode())
    monkeypatch.setattr(settings(),'otp_delivery_mode','console')
    seed_research(engine)
    headers,run=start(client)
    consent=client.post('/api/journey/consents',headers=headers,json={'purpose':'insurer_share','recipients':[run['items'][0]['plan']['insurer_id']],'accepted':True,'wording_version':'journey-sharing-v1'}).json()
    assert client.post('/api/journey/selection',headers=headers,json={'run_id':run['run_id'],'expected_version':1,'plan_ids':[run['items'][0]['id']],'insurer_consent_id':consent['id']}).status_code==200
    return headers


def request_code(client,headers,number='visitor@example.test'):
    return client.post('/api/journey/verify/start',headers=headers,json={'channel':'email','country_code':'+44','number':number,'consent':True})


def test_international_normalisation_and_official_payload(monkeypatch):
    assert destination('whatsapp','+44','07400 123456')=='+447400123456'
    assert destination('whatsapp','+91','9876543210')=='+919876543210'
    with pytest.raises(Exception):
        destination('whatsapp','+44','12')
    captured={}
    class Response:
        status_code=200
        def json(self):
            return {'messages':[{'id':'fixture'}]}
    class Client:
        def __init__(self,**kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self,*args):
            pass
        def post(self,url,**kwargs):
            captured.update(url=url,**kwargs)
            return Response()
    import app.journey.verification as verification
    monkeypatch.setattr(verification.httpx,'Client',Client)
    for field,value in {'whatsapp_access_token':'fixture-only','whatsapp_phone_number_id':'123456','whatsapp_graph_version':'v99.0','whatsapp_auth_template':'fixture_auth'}.items():
        monkeypatch.setattr(settings(),field,value)
    WhatsAppCloudProvider().send('+447400123456','123456','fixture-contact')
    assert captured['json']['template']['components'][1]['sub_type']=='url'
    assert captured['json']['template']['components'][0]['parameters'][0]['text']=='123456'


def test_otp_is_hashed_encrypted_bound_consumed_and_private(fixture_client,monkeypatch,capsys):
    client,_,engine=fixture_client
    headers=prepare(client,engine,monkeypatch)
    assert request_code(client,headers).status_code==200
    code=client.get('/api/journey/verify/demo-code',headers=headers).json()['code']
    ident=client.get('/api/journey/verify/status',headers=headers).json()['contact_id']
    assert client.post('/api/journey/contacts/verify',headers=headers,json={'contact_id':ident,'code':code}).status_code==409
    assert request_code(client,headers).status_code==429
    assert client.get('/api/journey/verify/demo-code').status_code==404
    with Session(engine) as db:
        contact=db.scalar(select(Contact))
        assert contact.data['challenge_hash']!=code
        assert 'code' not in contact.data
        raw=db.scalar(text('select data from journey_contact'))
        assert 'visitor@example.test' not in raw and 'challenge_hash' not in raw
        assert json.loads(raw)['format']=='fernet-v1'
    result=client.post('/api/journey/verify/check',headers=headers,json={'code':code})
    assert result.status_code==200 and not result.json()['real_ownership_verified']
    assert 'HttpOnly' in result.headers['set-cookie'] and 'SameSite=strict' in result.headers['set-cookie']
    assert client.post('/api/journey/verify/check',headers=headers,json={'code':code}).status_code==410
    assert client.get('/api/journey/verify/demo-code',headers=headers).status_code==410
    output=capsys.readouterr().out
    assert code not in output and 'visitor@example.test' not in output


def test_attempts_expiry_persisted_send_caps_and_csrf(fixture_client,monkeypatch):
    client,_,engine=fixture_client
    headers=prepare(client,engine,monkeypatch)
    assert request_code(client,{**headers,'Origin':'https://unrelated.example'}).status_code==403
    assert request_code(client,headers).status_code==200
    code=client.get('/api/journey/verify/demo-code',headers=headers).json()['code']
    wrong=f'{(int(code)+1)%1000000:06}'
    for _ in range(5):
        assert client.post('/api/journey/verify/check',headers=headers,json={'code':wrong}).status_code==422
    assert client.post('/api/journey/verify/check',headers=headers,json={'code':code}).status_code==429
    for _ in range(2):
        with Session(engine) as db:
            for row in db.scalars(select(OtpWindow)):
                row.data={**row.data,'sends':[(now()-timedelta(seconds=61)).isoformat() for _ in row.data['sends']]}
            db.commit()
        assert request_code(client,headers).status_code==200
    with Session(engine) as db:
        for row in db.scalars(select(OtpWindow)):
            row.data={**row.data,'sends':[(now()-timedelta(seconds=61)).isoformat() for _ in row.data['sends']]}
        contact=db.scalars(select(Contact).order_by(Contact.created_at.desc())).first()
        contact.data={**contact.data,'expires_at':(now()-timedelta(seconds=1)).isoformat()}
        db.commit()
    assert request_code(client,headers).status_code==429
    latest=client.get('/api/journey/verify/status',headers=headers).json()
    assert latest['attempts_left']==5
    assert client.post('/api/journey/verify/check',headers=headers,json={'code':'123456'}).status_code==410
