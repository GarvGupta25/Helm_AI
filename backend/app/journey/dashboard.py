from copy import deepcopy
from io import BytesIO
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import Field
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import session
from ..models import now
from ..public_assistant import _check_rate_limit
from .access import dashboard_case, same_origin
from .case_models import Document, Grant, Job, Quotation, QuoteRequest
from .cases import audit, present_case
from .narration import narrate
from .policy import Question, answer
from .schemas import Strict

router = APIRouter(prefix="/api/journey", tags=["synthetic quote dashboard"])


@router.post('/dashboard/notifications/stop')
def stop_notifications(request: Request, case=Depends(dashboard_case), db: Session = Depends(session)):
    same_origin(request)
    data = deepcopy(case.data)
    data['preferences']['channels'] = ['dashboard']
    for consent in data['consents']:
        if consent['purpose'].startswith('notify_'):
            consent['revoked'] = True
    case.data = data
    for job in db.scalars(select(Job).where(Job.case_id == case.id, Job.status == 'queued')):
        job.status = 'cancelled'
    audit(case, 'notifications_stopped')
    db.commit()
    return {'notice': 'Notifications stopped. Your private dashboard remains available.'}


def quotation_owned(db, case, ident):
    row = db.scalar(select(Quotation).join(QuoteRequest).where(Quotation.id == ident, QuoteRequest.case_id == case.id))
    if not row:
        raise HTTPException(404, 'Quotation unavailable')
    return row


@router.get('/dashboard')
def dashboard(case=Depends(dashboard_case), db: Session = Depends(session)):
    from datetime import timezone
    rows = db.scalars(select(Quotation).join(QuoteRequest).where(QuoteRequest.case_id == case.id)).all()
    active_link=db.scalar(select(Grant).where(Grant.case_id==case.id,Grant.kind=='magic_link',Grant.revoked.is_(False)))
    from .explanations import explanation, main_differences
    current=[row for row in rows if row.expires_at.replace(tzinfo=timezone.utc)>now()]
    return {**present_case(db, case), 'quotations': [{'id': row.id, 'item': row.data['item'], 'expires_at': row.expires_at,
        'explanation':explanation(row.data['item'],case.data['profile_version']),
        'status': 'expired' if row.expires_at.replace(tzinfo=timezone.utc) <= now() else 'received'} for row in rows],
        'messages': [m for m in case.data.get('messages', []) if m.get('audience') == 'customer'],
        'plan_requests':[{'plan_id':item['id'],'name':item['plan']['name'],'status':'received' if any(q.plan_id==item['id'] for q in rows) else request.status}
            for request in db.scalars(select(QuoteRequest).where(QuoteRequest.case_id==case.id)) for item in request.data['items']],
        'access_expires_at':active_link.expires_at if active_link else None,
        'main_differences':main_differences([row.data['item'] for row in current]),
        'notifications_enabled':any(c.get('purpose','').startswith('notify_') and not c.get('revoked') for c in case.data['consents'])}


def pdf_document(case, quotation):
    output = BytesIO()
    pdf = canvas.Canvas(output)
    pdf.setTitle('Helm AI synthetic quotation')
    item = quotation.data['item']
    lines = ['Helm AI - Synthetic quotation', 'SIMULATION: no payment, policy or insurance contract.',
        'Case reference: '+case.id, 'Quotation reference: '+quotation.id, 'Plan: '+item['plan']['name'],
        'Catalogue: '+item['plan']['version'], f"Confirmed profile version: {case.data['profile_version']}",
        f"Monthly base GBP {item['quote']['base_pence']/100:.2f}; assumed tax GBP {item['quote']['tax_pence']/100:.2f}",
        f"Monthly total GBP {item['quote']['monthly_pence']/100:.2f}; annual GBP {item['quote']['annual_pence']/100:.2f}",
        f"Excess GBP {item['plan']['excess_pence']/100:.2f}; copayment {item['plan']['copay']*100:g}%",
        'Existing-condition status: '+item['plan']['pre_existing'], 'Underwriting: '+item['plan']['underwriting'],
        'Fictional hospital list: '+str(item['plan']['network']), 'Referral: '+item['plan']['referral'],
        'Expires: '+quotation.expires_at.isoformat(), 'Generated: '+now().isoformat()]
    lines += [f"{care.replace('_', ' ')}: "+(f'GBP {value/100:.2f} annual eligible cap' if value else 'excluded / zero benefit') for care, value in item['plan']['limits'].items()]
    lines += [item['plan'].get('family_terms', {}).get('rating', ''), 'General information, not personal advice. Ask a broker about unknown terms.']
    y = 800
    for line in lines:
        for wrapped in simpleSplit(line, 'Helvetica', 10, 490):
            if y < 55:
                pdf.showPage()
                y = 800
            pdf.setFont('Helvetica', 10)
            pdf.drawString(50, y, wrapped)
            y -= 16
    pdf.save()
    return output.getvalue()


@router.get('/quotations/{quotation_id}/document')
def download(quotation_id: str, case=Depends(dashboard_case), db: Session = Depends(session)):
    row = quotation_owned(db, case, quotation_id)
    document = db.get(Document, row.document_id)
    if not document or document.ai_drafted or document.case_id != case.id:
        raise HTTPException(403, 'This document is not an authorized synthetic quotation')
    return Response(pdf_document(case, row), media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename="helm-demo-quote-{row.id}.pdf"', 'Cache-Control': 'no-store'})


@router.post('/quotations/{quotation_id}/questions')
def question(quotation_id: str, body: Question, case=Depends(dashboard_case), db: Session = Depends(session)):
    _check_rate_limit('dashboard-policy:'+case.id+':'+quotation_id)
    return answer(quotation_owned(db, case, quotation_id).data['item'], body.question)


@router.get('/dashboard/comparison/document')
def comparison_document(case=Depends(dashboard_case),db:Session=Depends(session)):
    from .explanations import main_differences
    rows=db.scalars(select(Quotation).join(QuoteRequest).where(QuoteRequest.case_id==case.id,Quotation.expires_at>now())).all()
    if len(rows)<2:
        raise HTTPException(422,'Two current received quotations are needed for a comparison PDF')
    for row in rows:
        document=db.get(Document,row.document_id)
        if not document or document.ai_drafted or document.case_id!=case.id:
            raise HTTPException(403,'Only authorised synthetic quotations may be exported')
    output=BytesIO()
    pdf=canvas.Canvas(output)
    pdf.setTitle('Helm AI synthetic quotation comparison')
    lines=['Helm AI - Synthetic quotation comparison','SIMULATION: no payment, policy or real insurance offer.',f"Case {case.id}; confirmed profile version {case.data['profile_version']}",'Generated '+now().isoformat(),main_differences([row.data['item'] for row in rows])]
    for row in rows:
        item=row.data['item']
        lines += [item['plan']['name'],f"Monthly GBP {item['quote']['monthly_pence']/100:.2f}; annual GBP {item['quote']['annual_pence']/100:.2f}; excess GBP {item['plan']['excess_pence']/100:.2f}",f"Existing conditions {item['plan']['pre_existing']}; fictional hospital tier {item['plan']['network']}."]
    y=800
    for line in lines:
        for wrapped in simpleSplit(line,'Helvetica',10,490):
            if y<55:
                pdf.showPage()
                y=800
            pdf.setFont('Helvetica',10)
            pdf.drawString(50,y,wrapped)
            y-=16
    pdf.save()
    return Response(output.getvalue(),media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="helm-demo-comparison.pdf"','Cache-Control':'no-store'})


class DashboardQuestion(Strict):
    mode: Literal['explain','compare','recommend'] = 'explain'
    question: str = Field(min_length=1,max_length=1000)
    quotation_ids: list[str] = Field(min_length=1,max_length=3)
    external_processing_consent: bool = False


@router.post('/dashboard/chat')
def dashboard_chat(body:DashboardQuestion,request:Request,case=Depends(dashboard_case),db:Session=Depends(session)):
    same_origin(request)
    _check_rate_limit('dashboard-chat:'+case.id)
    from .explanations import main_differences
    rows=[quotation_owned(db,case,ident) for ident in body.quotation_ids]
    if len(set(body.quotation_ids))!=len(rows) or any(row.expires_at.replace(tzinfo=now().tzinfo)<=now() for row in rows):
        raise HTTPException(422,'Choose distinct, current received quotations')
    import re
    if re.search(r'ignore|system|override|guarantee|diagnos|jailbreak|<|https?://|worldwide|waiting|implant|medication',body.question,re.I):
        return {'kind':'unknown','reply':'This snapshot cannot establish that answer. Ask your broker; no coverage, eligibility or price has been guessed.','citations':[],'provider_called':False}
    if body.mode=='explain':
        return answer(rows[0].data['item'],body.question)
    items=[row.data['item'] for row in rows]
    if body.mode=='compare':
        if len(items)<2:
            raise HTTPException(422,'Choose two or three quotations to compare')
        return {'kind':'facts',**narrate(main_differences(items)+' General information, not personal advice.',body.external_processing_consent),'citations':[{'field':'quotation.'+row.id+'.quote/plan','value':{'quote':row.data['item']['quote'],'excess_pence':row.data['item']['plan']['excess_pence'],'outpatient_pence':row.data['item']['plan']['limits']['outpatient'],'hospital_list':row.data['item']['plan']['network']}} for row in rows]}
    best=min(items,key=lambda i:(-i['fusion'],i['quote']['monthly_pence'],i['id']))
    return {'kind':'facts',**narrate(f"Among these current quotations, {best['plan']['name']} has the highest stored deterministic fit for the confirmed profile. It meets the saved hard requirements; its fictional monthly premium is {best['quote']['monthly_pence']/100:.2f} GBP. Existing conditions are never assumed covered. Ask a broker to review the limitations. General information, not personal advice.",body.external_processing_consent),'citations':[{'field':'confirmed_profile.version','value':case.data['profile_version']},{'field':'ranking.fusion','value':[{ 'id':i['id'],'fusion':i['fusion']} for i in items]},{'field':'quote.monthly_pence','value':best['quote']['monthly_pence']}],'method':'stored_deterministic_ranking'}


@router.post('/quotations/{quotation_id}/flag-question')
def flag(quotation_id: str, body: Question, request: Request, case=Depends(dashboard_case), db: Session = Depends(session)):
    same_origin(request)
    row = quotation_owned(db, case, quotation_id)
    data = deepcopy(case.data)
    questions = list(data.get('flagged_questions', []))
    if len(questions) >= 20:
        raise HTTPException(409, 'Up to 20 questions can be saved')
    questions.append({'question': body.question, 'plan_id': row.plan_id, 'profile_version': data['profile_version']})
    data['flagged_questions'] = questions
    case.data = data
    audit(case, 'customer_saved_policy_question', quotation_id=row.id)
    db.commit()
    return {'notice': 'Saved privately. Only an assigned broker with your current sharing consent can see it.'}
