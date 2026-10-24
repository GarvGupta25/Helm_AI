from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session
from test_journey_review import document_case, exact, ready

from app.journey.case_models import Case, Job
from app.journey.notifications import process_notifications
from app.journey.router import digest
from app.models import now


def test_traceability_audit_rejection_export_and_edit(fixture_client):
    client, engine, _, _, path, data = document_case(fixture_client)
    analysis=client.get(path+'/assistant').json()
    assert analysis['provider_called'] is False
    assert len(analysis['checklist'])==5
    doc=next(d for d in data['documents'] if d['ai_drafted'])
    draft=doc['draft']
    assert digest(draft['text'])==draft['generation']['output_hash']
    assert draft['generation']['input_hash']==digest(draft['statements'])
    assert all(fact['source'] in draft['sources'] and fact['text'] in draft['text'] for fact in draft['statements'])
    assert any(fact['source'].startswith('quotation:') for fact in draft['statements'])
    assert client.get(path+'/documents/'+doc['id']+'/export').status_code==403
    data=ready(client,path,data)
    ident,body=exact(data)
    docpath=path+'/documents/'+ident
    assert client.post(docpath+'/review',json={**body,'decision':'reject'}).status_code==422
    data=client.post(docpath+'/review',json={**body,'decision':'reject','notes':'Resolve uncertainty first'}).json()
    assert data['audit'][-1]['details']['review_notes']=='Resolve uncertainty first'
    data=ready(client,path,data)
    _,body=exact(data)
    data=client.post(docpath+'/review',json={**body,'decision':'approve'}).json()
    assert data['audit'][-1]['details']['checklist'] and data['audit'][-1]['details']['reviewed_at']
    export=client.get(docpath+'/export')
    assert export.status_code==200 and export.text==draft['text']
    assert export.headers['cache-control']=='no-store'
    _,body=exact(data)
    client.post(docpath+'/edit',json={**body,'text':'Human revised this draft.'})
    assert client.get(docpath+'/export').status_code==403
    with Session(engine) as db:
        assert not db.scalar(select(Job).where(Job.kind=='approved_dispatch'))


def test_assigned_priorities_and_internal_followup_withdrawal(fixture_client):
    client,engine,headers,consent,path,data=document_case(fixture_client)
    queue=client.get('/api/journey/broker/assistant/queue').json()
    assert queue['items'][0]['case_id']==data['id'] and queue['items'][0]['prepared_count']==1
    response=client.post(path+'/follow-up',json={'expected_version':data['version'],'hours':1})
    assert response.status_code==200,response.text
    with Session(engine) as db:
        job=db.scalar(select(Job).where(Job.kind=='broker_followup'))
        assert job.status=='queued' and job.data['external_sent'] is False
        process_notifications(db,clock=now()+timedelta(hours=1,seconds=1))
    assert any('Review this consented case' in i['text'] for i in client.get('/api/journey/broker/inbox').json()['items'])
    client.delete('/api/journey/consents/'+consent['id'],headers=headers)
    assert client.get(path+'/assistant').status_code==404
    assert client.get('/api/journey/broker/assistant/queue').json()['items']==[]
    assert client.get('/api/journey/broker/inbox').json()['items']==[]
    with Session(engine) as db:
        assert any(c.get('revoked') for c in db.get(Case,data['id']).data['consents'] if c['id']==consent['id'])
