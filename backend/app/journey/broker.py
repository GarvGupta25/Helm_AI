"""Assigned, consented broker access. Never an all-broker customer directory."""
import os
from copy import deepcopy
from datetime import timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import User, require_broker
from ..db import session
from ..models import now, uid
from .access import dashboard_case, same_origin
from .case_models import Case, Contact, Document, Grant, Job
from .cases import active, audit, live_case, present_case, source_current
from .contact import contact_owned
from .router import digest, owned
from .schemas import Strict

router = APIRouter(prefix='/api/journey', tags=['consented broker workspace'])
TRANSITIONS = {
    'new': {'triaged', 'closed'}, 'triaged': {'in_progress', 'closed'},
    'in_progress': {'awaiting_customer', 'awaiting_insurer', 'ready_for_signoff', 'closed'},
    'awaiting_customer': {'in_progress', 'closed'}, 'awaiting_insurer': {'in_progress', 'closed'},
    'ready_for_signoff': {'in_progress', 'closed'}, 'submitted': {'closed'}, 'closed': set(),
}


def assigned(db, user, ident):
    row = db.scalar(select(Case).where(Case.id == ident, Case.broker_id == user.id).with_for_update())
    if not row or not active(row, 'broker_share', ['helm-demo-broker']):
        raise HTTPException(404, 'Assigned case unavailable')
    return live_case(row)


def expected(case, version):
    if case.version != version:
        raise HTTPException(409, 'The case changed. Refresh before making this action.')
    if case.status == 'closed':
        raise HTTPException(409, 'This case is closed')


class Handoff(Strict):
    contact_id: str
    consent_id: str
    expected_version: int
    demo_acknowledged: Literal[True]


@router.post('/broker-handoff')
def early_handoff(body: Handoff, record=Depends(owned), db: Session = Depends(session)):
    contact = contact_owned(db, record, body.contact_id)
    consent = next((c for c in record.data.get('sharing_consents', []) if c['id'] == body.consent_id and c['purpose'] == 'broker_share' and c['recipients'] == ['helm-demo-broker'] and not c.get('revoked') and c['profile_version'] == record.version), None)
    if not contact.verified_at or not consent or record.version != body.expected_version:
        raise HTTPException(422, 'Verify a contact and explicitly share the current reviewed profile')
    key = digest([record.id, record.version, 'early_broker'])
    row = db.scalar(select(Case).where(Case.request_key == key))
    if row:
        return present_case(db, live_case(row))
    row = Case(session_id=record.id, contact_id=contact.id, request_key=key, broker_id=os.getenv('JOURNEY_DEMO_BROKER_ID') or None,
               expires_at=now()+timedelta(days=7), data={'profile_version': record.version, 'profile': record.data.get('confirmed', {}),
               'selected': [], 'consents': [consent], 'contact_ids': [contact.id], 'preferences': {'channels': ['dashboard'], 'quiet_start': 22, 'quiet_end': 8, 'time_zone': 'Europe/London'},
               'flagged_questions': record.data.get('flagged_questions', []), 'notes': [], 'messages': [], 'audit': [], 'trigger': 'early_broker_request'})
    db.add(row)
    db.flush()
    audit(row, 'early_broker_handoff_confirmed')
    db.commit()
    return present_case(db, row)


@router.post('/dashboard/broker-handoff')
def dashboard_handoff(request: Request, case=Depends(dashboard_case), db: Session = Depends(session)):
    same_origin(request)
    if case.status == 'closed':
        raise HTTPException(409, 'This case is closed')
    data = deepcopy(case.data)
    if not active(case, 'broker_share'):
        data['consents'].append({'id': uid(), 'purpose': 'broker_share', 'recipients': ['helm-demo-broker'], 'accepted': True, 'revoked': False,
                                 'wording_version': 'journey-sharing-v1', 'at': now().isoformat(), 'profile_version': data['profile_version']})
    case.data = data
    case.broker_id = case.broker_id or os.getenv('JOURNEY_DEMO_BROKER_ID') or None
    audit(case, 'dashboard_broker_handoff_confirmed')
    db.commit()
    return {'notice': 'Shared with your assigned demo broker.' if case.broker_id else 'Broker sharing recorded. Pending administrator assignment; no broker can see this case yet.'}


@router.post('/dashboard/broker-sharing/withdraw')
def dashboard_withdraw(request: Request, case=Depends(dashboard_case), db: Session = Depends(session)):
    same_origin(request)
    data = deepcopy(case.data)
    for consent in data['consents']:
        if consent['purpose'] == 'broker_share':
            consent['revoked'] = True
    case.data = data
    audit(case, 'broker_sharing_withdrawn')
    db.commit()
    return {'withdrawn': True}


@router.get('/broker/me')
def me(user: User = Depends(require_broker)):
    return {'id': user.id, 'role': 'broker'}


@router.get('/broker/cases')
def queue(status: str = '', urgency: Literal['all', 'expiring'] = 'all', search: str = Query(default='', max_length=36), offset: int = Query(default=0, ge=0),
          limit: int = Query(default=20, ge=1, le=50), user: User = Depends(require_broker), db: Session = Depends(session)):
    query = select(Case).where(Case.broker_id == user.id, Case.expires_at > now()).order_by(Case.expires_at, Case.id)
    if status:
        query = query.where(Case.status == status)
    if search:
        query = query.where(Case.id.startswith(search, autoescape=True))
    if urgency == 'expiring':
        query = query.where(Case.expires_at <= now()+timedelta(hours=24))
    # Scope before counts and pagination; encrypted consent stays authoritative.
    rows = [r for r in db.scalars(query) if not r.data.get('withdrawn') and active(r, 'broker_share', ['helm-demo-broker'])]
    return {'total': len(rows), 'items': [{'id': r.id, 'state': r.status, 'version': r.version, 'expires_at': r.expires_at,
            'urgency': 'expiring' if r.expires_at.replace(tzinfo=timezone.utc) < now()+timedelta(hours=24) else 'normal',
            'notice': 'Consented case ready for review'} for r in rows[offset:offset+limit]]}


def detail(db, case):
    contacts = db.scalars(select(Contact).where(Contact.id.in_(case.data['contact_ids']))).all()
    documents = db.scalars(select(Document).where(Document.case_id == case.id)).all()
    return {**present_case(db, case), 'contacts': [{'id': c.id, 'channel': c.channel, 'destination': c.data['destination'], 'verified_in_demo': bool(c.verified_at)} for c in contacts],
            'preferences': case.data['preferences'], 'questions': case.data.get('flagged_questions', []), 'notes': case.data.get('notes', []),
            'messages': case.data.get('messages', []), 'audit': case.data['audit'], 'checklist': case.data.get('checklist', {}),
            'documents': [{'id': d.id, 'kind': d.kind, 'revision': d.revision, 'hash': d.content_hash, 'ai_drafted': d.ai_drafted,
                           'draft': d.data if d.ai_drafted else {'notice': 'Synthetic quotation snapshot'}} for d in documents],
            'allowed_states': sorted(TRANSITIONS[case.status])}


@router.get('/broker/cases/{case_id}')
def get_case(case_id: str, user: User = Depends(require_broker), db: Session = Depends(session)):
    return detail(db, assigned(db, user, case_id))


class Transition(Strict):
    expected_version: int
    state: str = Field(max_length=32)
    reason: str = Field(default='', max_length=300)
    checklist: dict[Literal['profile', 'quotations', 'questions', 'documents'], bool] = Field(default_factory=dict)


@router.post('/broker/cases/{case_id}/transition')
def transition(case_id: str, body: Transition, user: User = Depends(require_broker), db: Session = Depends(session)):
    case = assigned(db, user, case_id)
    expected(case, body.expected_version)
    if body.state not in TRANSITIONS[case.status] or (body.state == 'closed' and not body.reason.strip()):
        raise HTTPException(422, 'This transition is not allowed, or a closing reason is missing')
    if body.state == 'ready_for_signoff':
        source_current(db, case)
        if set(body.checklist) != {'profile', 'quotations', 'questions', 'documents'} or not all(body.checklist.values()):
            raise HTTPException(422, 'Review every sign-off checklist item')
        if not db.scalar(select(Document.id).where(Document.case_id == case.id, Document.ai_drafted.is_(True))):
            raise HTTPException(422, 'Prepare a review document before sign-off')
    data = deepcopy(case.data)
    data['checklist'] = body.checklist
    if body.state == 'closed':
        data['close_reason'] = body.reason
        for grant in db.scalars(select(Grant).where(Grant.case_id == case.id)):
            grant.revoked = True
        for job in db.scalars(select(Job).where(Job.case_id == case.id, Job.status == 'queued')):
            job.status = 'cancelled'
    case.data = data
    previous = case.status
    case.status = body.state
    audit(case, 'case_transition', user.id, before=previous, after=body.state)
    db.commit()
    return detail(db, case)


class Text(Strict):
    expected_version: int
    text: str = Field(min_length=1, max_length=3000)


@router.post('/broker/cases/{case_id}/notes')
def note(case_id: str, body: Text, user: User = Depends(require_broker), db: Session = Depends(session)):
    case = assigned(db, user, case_id)
    expected(case, body.expected_version)
    data = deepcopy(case.data)
    if len(data['notes']) >= 100:
        raise HTTPException(409, 'Demo note capacity reached')
    data['notes'].append({'id': uid(), 'text': body.text, 'by': user.id, 'at': now().isoformat()})
    case.data = data
    audit(case, 'private_note_added', user.id)
    db.commit()
    return detail(db, case)


@router.post('/broker/cases/{case_id}/messages')
def broker_message(case_id: str, body: Text, user: User = Depends(require_broker), db: Session = Depends(session)):
    case = assigned(db, user, case_id)
    expected(case, body.expected_version)
    data = deepcopy(case.data)
    if len(data['messages']) >= 100:
        raise HTTPException(409, 'Demo message capacity reached')
    data['messages'].append({'id': uid(), 'text': body.text, 'by': user.id, 'authorship': 'human', 'audience': 'customer', 'at': now().isoformat()})
    case.data = data
    audit(case, 'human_broker_message_sent', user.id)
    db.commit()
    return detail(db, case)


@router.post('/dashboard/messages')
def customer_message(body: Text, request: Request, case=Depends(dashboard_case), db: Session = Depends(session)):
    same_origin(request)
    expected(case, body.expected_version)
    if not active(case, 'broker_share', ['helm-demo-broker']):
        raise HTTPException(403, 'Share this case with the broker before sending a message')
    data = deepcopy(case.data)
    if len(data['messages']) >= 100:
        raise HTTPException(409, 'Demo message capacity reached')
    data['messages'].append({'id': uid(), 'text': body.text, 'by': 'customer', 'audience': 'customer', 'at': now().isoformat()})
    case.data = data
    audit(case, 'customer_message_received')
    db.commit()
    return {'sent_in_demo': True}
