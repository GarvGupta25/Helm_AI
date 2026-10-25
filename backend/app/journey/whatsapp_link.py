"""Deliver the existing private dashboard capability after verified OTP proof."""
from datetime import timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import session
from ..models import now
from .access import same_origin
from .case_models import Grant, Job
from .router import owned
from .twilio_auth import AUTH_MODES, mock_enabled, send_link
from .verification import current_contact
from .wizard_access import Access, create

router = APIRouter(prefix='/api/journey/verify', tags=['WhatsApp private access'])


def issue_verified_link(request, record, db):
    contact = current_contact(db, record)
    if (contact.data.get('mode') not in AUTH_MODES or not contact.verified_at
            or record.data.get('wizard_verified_contact') != contact.id):
        raise HTTPException(403, 'Complete WhatsApp verification first')
    if contact.verified_at.replace(tzinfo=timezone.utc) <= now()-timedelta(minutes=10):
        raise HTTPException(410, 'Verification proof expired; verify again before requesting a link')
    # Reuse the existing reviewed selection, sharing consents, case and hashed grant.
    result = create(Access(hours=24, notifications=False), request, record, db)
    grant = db.get(Grant, record.data['wizard_access']['grant_id'])
    job = db.scalar(select(Job).where(Job.dedupe_key == 'access:' + grant.id).with_for_update())
    if not job.data.get('auth_delivery'):
        # Reserve before networking. A timeout must never cause an automatic duplicate send.
        job.data = {**job.data, 'auth_delivery': True, 'provider_status': 'pending'}
        db.commit()
        if mock_enabled():
            delivery = {'provider_status': 'mock', 'external_sent': False,
                        'notice': 'Simulation only. Open the private developer inbox to retrieve your link.'}
        else:
            delivery = send_link(db, contact, result['url'])
        job.data = {**job.data, **delivery}
        db.commit()
    return {'case_id': result['case_id'], 'expires_at': result['expires_at'],
            'delivery_status': job.data['provider_status'],
            'notice': job.data.get('notice', 'Link submission is pending. Check your phone before reverifying.')}


@router.post('/magic-link')
def issue(request: Request, record=Depends(owned), db: Session = Depends(session)):
    same_origin(request)
    return issue_verified_link(request, record, db)


@router.get('/magic-link')
def status(record=Depends(owned), db: Session = Depends(session)):
    contact = current_contact(db, record)
    if not contact.verified_at or record.data.get('wizard_verified_contact') != contact.id:
        raise HTTPException(403, 'Verify your WhatsApp number first')
    metadata = record.data.get('wizard_access', {})
    grant = db.get(Grant, metadata.get('grant_id', ''))
    job = db.scalar(select(Job).where(Job.dedupe_key == 'access:' + grant.id)) if grant else None
    if not grant or not job or not job.data.get('auth_delivery'):
        raise HTTPException(404, 'No authentication link requested')
    return {'delivery_status': job.data.get('provider_status'), 'expires_at': grant.expires_at,
            'expired': grant.revoked or grant.expires_at.replace(tzinfo=now().tzinfo) <= now(),
            'notice': job.data.get('notice', 'Awaiting provider delivery status.')}


@router.get('/mock-link')
def developer_link(record=Depends(owned), db: Session = Depends(session)):
    if not mock_enabled():
        raise HTTPException(404, 'Developer inbox unavailable')
    contact = current_contact(db, record)
    if not contact.verified_at or record.data.get('wizard_verified_contact') != contact.id:
        raise HTTPException(403, 'Verify the simulated contact first')
    grant = db.get(Grant, record.data.get('wizard_access', {}).get('grant_id', ''))
    if not grant or grant.used or grant.revoked or grant.expires_at.replace(tzinfo=now().tzinfo) <= now():
        raise HTTPException(410, 'Link unavailable')
    job = db.scalar(select(Job).where(Job.dedupe_key == 'access:' + grant.id))
    return {'url': job.data['url'], 'notice': 'Isolated developer inbox; not real phone verification.'}
