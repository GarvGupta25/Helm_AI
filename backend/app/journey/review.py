"""Human approval binds content, recipients, purpose and the confirmed profile."""
from copy import deepcopy
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import User, require_broker
from ..db import session
from ..models import now, uid
from .broker import assigned, detail, expected
from .case_models import Approval, Contact, Document, Job, Quotation, QuoteRequest
from .cases import active, audit, source_current
from .router import digest
from .schemas import Strict

router = APIRouter(prefix='/api/journey/broker/cases', tags=['exact revision human review'])


def authority(db, case, data):
    source_current(db, case)
    recipients = data['recipients']
    if data['audience'] == 'customer':
        contacts = db.scalars(select(Contact).where(Contact.id.in_(recipients), Contact.session_id == case.session_id)).all()
        if set(recipients) - set(case.data['contact_ids']) or len(contacts) != len(recipients) or not all(c.verified_at for c in contacts):
            raise HTTPException(403, 'Reviewed verified recipients changed')
    elif not active(case, 'insurer_share', recipients) or set(recipients) - {i['plan']['insurer_id'] for i in case.data['selected']}:
        raise HTTPException(403, 'The named insurer sharing consent is no longer active')
    if data['profile_version'] != case.data['profile_version']:
        raise HTTPException(409, 'Draft profile is stale')


def scope(document):
    return digest({key: document.data[key] for key in ('audience', 'recipients', 'profile_version', 'kind')})


def document_owned(db, case, ident):
    document = db.scalar(select(Document).where(Document.id == ident, Document.case_id == case.id, Document.ai_drafted.is_(True)).with_for_update())
    if not document:
        raise HTTPException(404, 'Review document unavailable')
    return document


def reviewable(case):
    if case.status not in {'in_progress', 'ready_for_signoff'}:
        raise HTTPException(409, 'Move this case into progress before preparing or editing review documents')


def current_quotations(db, case):
    if not case.data['selected']:
        return
    quotes = db.scalars(select(Quotation).join(QuoteRequest).where(QuoteRequest.case_id == case.id, Quotation.expires_at > now())).all()
    if {q.plan_id for q in quotes} != {i['id'] for i in case.data['selected']}:
        raise HTTPException(409, 'Receive current quotations for every selected plan before sign-off')


class Draft(Strict):
    expected_version: int
    kind: Literal['case_summary', 'information_request', 'insurer_request', 'cover_check', 'needs_summary', 'recommendation_rationale', 'quotation_comparison', 'underwriting_pack', 'customer_message', 'followup_message']
    audience: Literal['customer', 'insurer']
    recipients: list[str] = Field(min_length=1, max_length=3)


@router.post('/{case_id}/documents')
def draft(case_id: str, body: Draft, user: User = Depends(require_broker), db: Session = Depends(session)):
    case = assigned(db, user, case_id)
    expected(case, body.expected_version)
    reviewable(case)
    if len(db.scalars(select(Document.id).where(Document.case_id == case.id)).all()) >= 30:
        raise HTTPException(409, 'Demo document capacity reached')
    data = {'kind': body.kind, 'audience': body.audience, 'recipients': sorted(set(body.recipients)), 'profile_version': case.data['profile_version'],
            'sources': [f'case:{case.id}:profile:{case.data["profile_version"]}']+[f'plan:{i["id"]}:catalogue:{i["plan"]["version"]}' for i in case.data['selected']],
            'provider_called': False, 'draft_method': 'controlled_demo_template'}
    authority(db, case, data)
    from .broker_assistant import CHECKLIST, quotation_statements, statements
    facts=statements(case.data)+quotation_statements(db,case)
    data['sources'] += [fact['source'] for fact in facts]
    lines=['AI-DRAFTED, NEEDS BROKER REVIEW — INTERNAL UNTIL HUMAN APPROVAL', 'General information only. No real offer, policy, compliance certificate or submission.', 'Purpose: '+body.kind.replace('_',' ')]
    lines += [fact['text']+' [source: '+fact['source']+']' for fact in facts]
    lines.append('Human review required: verify missing facts, all exclusions, existing-condition uncertainty and recipient scope before signing.')
    data['statements']=facts
    data['text']='\n'.join(lines)
    data['generation']={'model':'controlled-source-template','prompt_version':'broker-draft-v2','input_references':data['sources'],'input_hash':digest(facts),'output_hash':digest(data['text']),'checklist_version':CHECKLIST['version'],'provider_called':False}
    document = Document(case_id=case.id, kind=body.kind, ai_drafted=True, data=data, content_hash=digest(data))
    db.add(document)
    db.flush()
    if case.status == 'ready_for_signoff':
        case.status = 'in_progress'
    audit(case, 'review_document_drafted', user.id, document_id=document.id, revision=1, generation=data['generation'])
    db.commit()
    return detail(db, case)


class Exact(Strict):
    expected_version: int
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r'^[0-9a-f]{64}$')


class Edit(Exact):
    text: str = Field(min_length=1, max_length=10000)


def exact(document, body):
    if document.revision != body.revision or document.content_hash != body.content_hash or digest(document.data) != document.content_hash:
        raise HTTPException(409, 'The exact document revision changed. Review it again.')


@router.post('/{case_id}/documents/{document_id}/edit')
def edit(case_id: str, document_id: str, body: Edit, user: User = Depends(require_broker), db: Session = Depends(session)):
    case = assigned(db, user, case_id)
    expected(case, body.expected_version)
    reviewable(case)
    document = document_owned(db, case, document_id)
    exact(document, body)
    document.data = {**deepcopy(document.data), 'text': body.text, 'edited_by': user.id}
    document.revision += 1
    document.content_hash = digest(document.data)
    for approval in db.scalars(select(Approval).where(Approval.document_id == document.id)):
        approval.revoked = True
    case.status = 'in_progress'
    audit(case, 'document_revision_edited', user.id, document_id=document.id, revision=document.revision)
    db.commit()
    return detail(db, case)


class Decision(Exact):
    decision: Literal['approve', 'reject']
    notes: str = Field(default='',max_length=1000)


@router.post('/{case_id}/documents/{document_id}/review')
def review(case_id: str, document_id: str, body: Decision, user: User = Depends(require_broker), db: Session = Depends(session)):
    case = assigned(db, user, case_id)
    expected(case, body.expected_version)
    if case.status != 'ready_for_signoff':
        raise HTTPException(409, 'Complete the sign-off checklist before approving')
    if body.decision=='reject' and not body.notes.strip():
        raise HTTPException(422,'Add revision notes when rejecting a draft')
    document = document_owned(db, case, document_id)
    exact(document, body)
    authority(db, case, document.data)
    current_quotations(db, case)
    for prior in db.scalars(select(Approval).where(Approval.document_id == document.id)):
        prior.revoked = True
    db.add(Approval(document_id=document.id, content_hash=document.content_hash, scope_hash=scope(document), approved_by=user.id, decision=body.decision))
    if body.decision == 'reject':
        case.status = 'in_progress'
    audit(case, 'document_'+body.decision, user.id, document_id=document.id, revision=document.revision, content_hash=document.content_hash,checklist=deepcopy(case.data.get('checklist',{})),review_notes=body.notes,reviewed_at=now().isoformat())
    db.commit()
    return detail(db, case)


@router.post('/{case_id}/documents/{document_id}/dispatch')
def dispatch(case_id: str, document_id: str, body: Exact, user: User = Depends(require_broker), db: Session = Depends(session)):
    case = assigned(db, user, case_id)
    expected(case, body.expected_version)
    if case.status != 'ready_for_signoff':
        raise HTTPException(409, 'This case is not ready for sign-off')
    document = document_owned(db, case, document_id)
    exact(document, body)
    authority(db, case, document.data)
    current_quotations(db, case)
    approval = db.scalar(select(Approval).where(Approval.document_id == document.id, Approval.content_hash == document.content_hash,
        Approval.scope_hash == scope(document), Approval.approved_by == user.id, Approval.decision == 'approve', Approval.revoked.is_(False)).with_for_update())
    if not approval:
        raise HTTPException(403, 'A human approval of this exact content and recipient scope is required')
    if document.data['audience'] == 'customer' and len(case.data['messages']) >= 100:
        raise HTTPException(409, 'Demo message capacity reached')
    for recipient in document.data['recipients']:
        db.add(Job(case_id=case.id, contact_id=recipient if document.data['audience'] == 'customer' else None, kind='approved_dispatch',
                   dedupe_key=f'approved:{approval.id}:{recipient}', status='delivered_demo', due_at=now(),
                   data={'text': document.data['text'], 'approval_id': approval.id, 'document_id': document.id, 'revision': document.revision,
                         'recipient': recipient, 'audience': document.data['audience'], 'external_sent': False, 'notice': 'Human-approved simulated delivery only.'}))
    if document.data['audience'] == 'customer':
        data = deepcopy(case.data)
        data['messages'].append({'id': uid(), 'text': document.data['text'], 'by': user.id, 'audience': 'customer', 'at': now().isoformat(), 'approval_id': approval.id})
        case.data = data
    case.status = 'submitted'
    audit(case, 'approved_demo_dispatch', user.id, document_id=document.id, revision=document.revision, approval_id=approval.id)
    db.commit()
    return detail(db, case)


@router.get('/{case_id}/documents/{document_id}/export')
def export_approved(case_id:str,document_id:str,user:User=Depends(require_broker),db:Session=Depends(session)):
    case=assigned(db,user,case_id)
    document=document_owned(db,case,document_id)
    authority(db,case,document.data)
    current_quotations(db,case)
    approval=db.scalar(select(Approval).where(Approval.document_id==document.id,Approval.content_hash==document.content_hash,Approval.scope_hash==scope(document),Approval.approved_by==user.id,Approval.decision=='approve',Approval.revoked.is_(False)))
    if not approval or digest(document.data)!=document.content_hash:
        raise HTTPException(403,'Only the exact human-approved document may be exported')
    return Response(document.data['text'],media_type='text/plain',headers={'Content-Disposition':f'attachment; filename="helm-approved-{document.id}-v{document.revision}.txt"','Cache-Control':'no-store'})
