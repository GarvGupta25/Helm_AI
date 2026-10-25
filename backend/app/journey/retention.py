"""Explicit, bounded demo retention. Cases outlive intake only with recorded consent."""
from datetime import timedelta

from sqlalchemy import select

from ..models import now
from .case_models import Approval, Case, Contact, Document, Grant, Job, OtpWindow, Quotation, QuoteRequest
from .models import JourneyRun, JourneySession, ProfileVersion


def delete_cases(db, cases):
    for case in cases:
        documents = db.scalars(select(Document).where(Document.case_id == case.id)).all()
        requests = db.scalars(select(QuoteRequest).where(QuoteRequest.case_id == case.id)).all()
        grants = db.scalars(select(Grant).where(Grant.case_id == case.id)).all()
        for grant in grants:
            if grant.parent_id:
                db.delete(grant)
        db.flush()
        for grant in grants:
            if not grant.parent_id:
                db.delete(grant)
        for job in db.scalars(select(Job).where(Job.case_id == case.id)):
            db.delete(job)
        for request in requests:
            for quotation in db.scalars(select(Quotation).where(Quotation.request_id == request.id)):
                db.delete(quotation)
        db.flush()
        for document in documents:
            for approval in db.scalars(select(Approval).where(Approval.document_id == document.id)):
                db.delete(approval)
        db.flush()
        for document in documents:
            db.delete(document)
        for request in requests:
            db.delete(request)
        db.flush()
        db.delete(case)
    db.flush()


def purge_expired(db, clock=None):
    clock = clock or now()
    expired = db.scalars(select(Case).where(Case.expires_at <= clock).limit(100).with_for_update(skip_locked=True)).all()
    delete_cases(db, expired)
    for row in db.scalars(select(JourneySession).where(JourneySession.expires_at <= clock).with_for_update(skip_locked=True)):
        if not row.data.get('purged'):
            for model in (JourneyRun, ProfileVersion):
                for snapshot in db.scalars(select(model).where(model.session_id == row.id)):
                    db.delete(snapshot)
            row.data = {'purged': True}
    for contact in db.scalars(select(Contact).where(Contact.created_at <= clock-timedelta(days=7))):
        if db.scalar(select(Case.id).where(Case.contact_id == contact.id)):
            continue
        # A secondary contact may also belong to a still-live case.
        if any(contact.id in c.data.get('contact_ids', []) for c in db.scalars(select(Case).where(Case.session_id == contact.session_id))):
            continue
        for grant in db.scalars(select(Grant).where(Grant.contact_id == contact.id, Grant.case_id.is_(None))):
            db.delete(grant)
        for job in db.scalars(select(Job).where(Job.contact_id == contact.id, Job.case_id.is_(None))):
            db.delete(job)
        db.flush()
        db.delete(contact)
    for window in db.scalars(select(OtpWindow).where(OtpWindow.expires_at <= clock).limit(100)):
        db.delete(window)
    from .funnel import purge_counts
    purge_counts(db,clock)
    db.commit()
    return len(expired)
