from copy import deepcopy
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import session
from ..models import now
from .access import dashboard_case, same_origin
from .case_models import Document, Grant, Job, Quotation, QuoteRequest
from .cases import audit, present_case
from .policy import Question, answer

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
    return {**present_case(db, case), 'quotations': [{'id': row.id, 'item': row.data['item'], 'expires_at': row.expires_at,
        'status': 'expired' if row.expires_at.replace(tzinfo=timezone.utc) <= now() else 'received'} for row in rows],
        'messages': [m for m in case.data.get('messages', []) if m.get('audience') == 'customer'],
        'plan_requests':[{'plan_id':item['id'],'name':item['plan']['name'],'status':'received' if any(q.plan_id==item['id'] for q in rows) else request.status}
            for request in db.scalars(select(QuoteRequest).where(QuoteRequest.case_id==case.id)) for item in request.data['items']],
        'access_expires_at':active_link.expires_at if active_link else None}


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
        'Expires: '+quotation.expires_at.isoformat()]
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
    return answer(quotation_owned(db, case, quotation_id).data['item'], body.question)


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
