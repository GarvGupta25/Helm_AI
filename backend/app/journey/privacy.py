"""Capability-authorised export and complete deletion of one demo journey."""
from typing import Literal

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import session
from .access import same_origin
from .case_models import Case, Contact, Grant, Job, OtpWindow
from .contact import keyed
from .models import JourneyRun, ProfileVersion
from .retention import delete_cases
from .router import owned, present
from .schemas import Strict
from .verification import demo_codes

router=APIRouter(prefix='/api/journey/privacy',tags=['visitor data controls'])


@router.get('/export')
def export(record=Depends(owned),db:Session=Depends(session)):
    contacts=db.scalars(select(Contact).where(Contact.session_id==record.id)).all()
    cases=db.scalars(select(Case).where(Case.session_id==record.id)).all()
    return {'notice':'Private fictional journey export. Store securely. Secret access tokens and verification material excluded.','current':present(record),'consents':record.data.get('sharing_consents',[]),
        'versions':[{'version':r.version,'data':r.data} for r in db.scalars(select(ProfileVersion).where(ProfileVersion.session_id==record.id))],
        'comparisons':[r.data for r in db.scalars(select(JourneyRun).where(JourneyRun.session_id==record.id))],
        'contacts':[{'channel':r.channel,'destination':r.data['destination'],'verified_at':r.verified_at} for r in contacts],
        'cases':[{'reference':r.id,'state':r.status,'profile':r.data['profile'],'selected':r.data['selected'],'consents':r.data['consents'],'messages':r.data.get('messages',[])} for r in cases]}


class Delete(Strict):
    confirm: Literal[True]


@router.post('/delete')
def delete(body:Delete,request:Request,record=Depends(owned),db:Session=Depends(session)):
    same_origin(request)
    delete_cases(db,db.scalars(select(Case).where(Case.session_id==record.id).with_for_update()).all())
    contacts=db.scalars(select(Contact).where(Contact.session_id==record.id)).all()
    for contact in contacts:
        grants=db.scalars(select(Grant).where(Grant.contact_id==contact.id)).all()
        for grant in grants:
            if grant.parent_id:
                db.delete(grant)
        db.flush()
        for grant in grants:
            if not grant.parent_id:
                db.delete(grant)
        for job in db.scalars(select(Job).where(Job.contact_id==contact.id)):
            db.delete(job)
        db.flush()
        demo_codes.pop(contact.id,None)
        db.delete(contact)
    for model in (JourneyRun,ProfileVersion):
        for row in db.scalars(select(model).where(model.session_id==record.id)):
            db.delete(row)
    window=db.get(OtpWindow,keyed('otp-session:'+record.id))
    if window:
        db.delete(window)
    db.flush()
    db.delete(record)
    db.commit()
    return {'deleted':True,'notice':'This journey, contacts and derived cases were deleted. Anonymous aggregate counts have no visitor identity and cannot be linked back to you.'}
