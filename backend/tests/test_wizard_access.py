from datetime import timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_wizard_verification import prepare, request_code

from app.journey.case_models import Contact, Grant, OtpWindow, QuoteRequest
from app.journey.worker import process_quotes
from app.models import now


def test_access_requires_current_verification_and_is_idempotent_with_private_exchange(fixture_client,monkeypatch):
    client,_,engine=fixture_client
    headers=prepare(client,engine,monkeypatch)
    assert client.post('/api/journey/wizard/access',headers=headers,json={'hours':24}).status_code==404
    request_code(client,headers)
    assert client.post('/api/journey/wizard/access',headers=headers,json={'hours':24}).status_code==422
    code=client.get('/api/journey/verify/demo-code',headers=headers).json()['code']
    client.post('/api/journey/verify/check',headers=headers,json={'code':code})
    before=now()
    response=client.post('/api/journey/wizard/access',headers=headers,json={'hours':48})
    assert response.status_code==200
    data=response.json()
    assert data['url'].startswith('/my-quotes#')
    again=client.post('/api/journey/wizard/access',headers=headers,json={'hours':48}).json()
    assert again['reused'] and again['url']==data['url']
    assert client.post('/api/journey/wizard/access',headers=headers,json={'hours':24}).status_code==409
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(QuoteRequest))==1
        grant=db.scalar(select(Grant).where(Grant.kind=='magic_link'))
        assert 47.99 <= (grant.expires_at.replace(tzinfo=timezone.utc)-before).total_seconds()/3600 <= 48.01
        assert grant.token_hash!=data['url'].split('#')[1]
        assert process_quotes(db,clock=now()+timedelta(seconds=10))==1
    exchanged=client.post('/api/journey/access-links/exchange',json={'token':data['url'].split('#')[1]})
    assert exchanged.status_code==200
    dashboard=client.get('/api/journey/dashboard')
    assert dashboard.headers['referrer-policy']=='no-referrer' and dashboard.headers['cache-control']=='no-store'
    assert dashboard.json()['plan_requests'][0]['status']=='received'
    assert dashboard.json()['access_expires_at']
    # Existing contacts recover through the same delivery policy, never plaintext jobs.
    with Session(engine) as db:
        for row in db.scalars(select(OtpWindow)):
            row.data={**row.data,'sends':[(now()-timedelta(seconds=61)).isoformat()]}
        db.commit()
    recovered=client.post('/api/journey/access-links/recover',json={'case_id':data['case_id'],'channel':'email','destination':'visitor@example.test'}).json()
    local=client.get('/api/journey/access-links/recovery-demo-code/'+recovered['contact_id'])
    assert local.status_code==200
    assert client.post('/api/journey/access-links/recover/verify',json={'case_id':data['case_id'],'contact_id':recovered['contact_id'],'code':local.json()['code']}).status_code==200
    assert client.get('/api/journey/dashboard').status_code==410
    with Session(engine) as db:
        assert db.scalar(select(Contact)).data['consumed']
