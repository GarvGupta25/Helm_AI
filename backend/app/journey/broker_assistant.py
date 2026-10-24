"""Internal source-linked drafts. Only assigned humans may approve delivery."""
import json
from datetime import timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import User, require_broker
from ..db import session
from ..models import now
from .broker import assigned, detail, expected, next_deadline
from .case_models import Case, Document, Job, Quotation, QuoteRequest
from .cases import active, audit
from .router import digest
from .schemas import JourneyProfile, Strict, completeness

router=APIRouter(prefix='/api/journey/broker',tags=['internal broker assistant'])
CHECKLIST=json.loads(Path(__file__).with_name('broker_checklist.json').read_text())


def statements(snapshot):
    result=[]
    profile=snapshot.get('profile',{})
    for field in ['people','location','cover','budget','excess','hospital_list','outpatient','benefits','health']:
        value=profile.get(field)
        result.append({'text':field.replace('_',' ').capitalize()+': '+json.dumps(value,ensure_ascii=False,sort_keys=True),'source':'profile.'+field,'value':value,'confidence':'review' if value in (None,{},[]) else 'source_fact'})
    for index,item in enumerate(snapshot.get('selected',[])):
        result.append({'text':f"{item['plan']['name']}: fictional monthly GBP {item['quote']['monthly_pence']/100:.2f}; excess GBP {item['plan']['excess_pence']/100:.2f}; existing conditions {item['plan']['pre_existing']}.",'source':f'selected.{index}','value':{'id':item['id'],'quote':item['quote'],'plan':item['plan']},'confidence':'source_fact'})
    for index,item in enumerate(snapshot.get('flagged_questions',[])):
        result.append({'text':'Unverified user-supplied question for human review: '+item['question'],'source':f'flagged_questions.{index}.question','value':item['question'],'confidence':'review'})
    return result


def quotation_statements(db,case):
    quotes=db.scalars(select(Quotation).join(QuoteRequest).where(QuoteRequest.case_id==case.id,Quotation.expires_at>now())).all()
    return [{'text':f"Received synthetic quotation: {q.data['item']['plan']['name']}, monthly GBP {q.data['item']['quote']['monthly_pence']/100:.2f}.",'source':f'quotation:{q.id}:document:{q.document_id}','value':q.data['item'],'confidence':'source_fact'} for q in quotes]


def analyse(db,case):
    profile=JourneyProfile.model_validate(case.data.get('profile',{}))
    check=completeness(profile,strict=False)
    quotes=db.scalars(select(Quotation).join(QuoteRequest).where(QuoteRequest.case_id==case.id,Quotation.expires_at>now())).all()
    docs=db.scalars(select(Document).where(Document.case_id==case.id,Document.ai_drafted.is_(True))).all()
    statuses={'profile':'missing' if check['missing'] else 'drafted','consent':'drafted' if active(case,'broker_share',['helm-demo-broker']) else 'conflicting','selection':'drafted' if case.data['selected'] else 'missing','quotations':'drafted' if case.data['selected'] and {q.plan_id for q in quotes}=={i['id'] for i in case.data['selected']} else 'missing','questions':'conflicting' if case.data.get('flagged_questions') else 'drafted'}
    return {'notice':CHECKLIST['notice'],'checklist_version':CHECKLIST['version'],'checklist':[{**rule,'status':statuses[rule['id']]} for rule in CHECKLIST['rules']],'missing_fields':check['missing'],'statements':statements(case.data)+quotation_statements(db,case),'prepared_documents':[{'id':d.id,'kind':d.kind,'revision':d.revision} for d in docs],'next_deadline':next_deadline(db,case),'provider_called':False,'method':'controlled_source_assembly','input_hash':digest({'profile_version':case.data['profile_version'],'profile':case.data['profile'],'selected':case.data['selected'],'questions':case.data.get('flagged_questions',[])})}


@router.get('/cases/{case_id}/assistant')
def assistant(case_id:str,user:User=Depends(require_broker),db:Session=Depends(session)):
    return analyse(db,assigned(db,user,case_id))


@router.get('/assistant/queue')
def queue_assistant(user:User=Depends(require_broker),db:Session=Depends(session)):
    cases=[case for case in db.scalars(select(Case).where(Case.broker_id==user.id,Case.expires_at>now(),Case.status!='closed')) if not case.data.get('withdrawn') and active(case,'broker_share',['helm-demo-broker'])]
    cases.sort(key=lambda case:(next_deadline(db,case),case.id))
    return {'notice':'Internal priorities only; no automatic customer or insurer action.','items':[{'case_id':case.id,'state':case.status,'next_deadline':next_deadline(db,case),'prepared_count':len(db.scalars(select(Document.id).where(Document.case_id==case.id,Document.ai_drafted.is_(True))).all())} for case in cases[:50]]}


class Followup(Strict):
    expected_version: int
    hours: int = 24


@router.post('/cases/{case_id}/follow-up')
def followup(case_id:str,body:Followup,user:User=Depends(require_broker),db:Session=Depends(session)):
    case=assigned(db,user,case_id)
    expected(case,body.expected_version)
    if body.hours not in {1,24,48}:
        raise HTTPException(422,'Choose a follow-up in 1, 24 or 48 hours')
    key=f'followup:{case.id}:{case.version}:{body.hours}'
    if not db.scalar(select(Job.id).where(Job.dedupe_key==key)):
        due=min(now()+timedelta(hours=body.hours),case.expires_at.replace(tzinfo=now().tzinfo))
        db.add(Job(case_id=case.id,kind='broker_followup',dedupe_key=key,status='queued',due_at=due,data={'broker_id':user.id,'text':'Review this consented case and consider the next human action.','external_sent':False}))
        audit(case,'internal_followup_scheduled',user.id,hours=body.hours)
        db.commit()
    return detail(db,case)
