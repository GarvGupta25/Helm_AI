"""Consent-bound, replay-safe selection before contact verification."""
from copy import deepcopy

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy.orm import Session

from ..db import session
from ..models import now, uid
from .compare import run_owned
from .router import digest, owned, save
from .schemas import Strict

router = APIRouter(prefix='/api/journey',tags=['reviewed selection'])


def consent_event(record, ident, purpose):
    event=next((c for c in record.data.get('sharing_consents',[]) if c['id']==ident and c['purpose']==purpose and not c.get('revoked') and c['profile_version']==record.version),None)
    if not event:
        raise HTTPException(422,'Review the current sharing consent before continuing')
    return event


def selected(record):
    value=record.data.get('wizard_selection')
    if not value:
        raise HTTPException(404,'Review a plan selection first')
    if value['profile_version']!=record.version:
        raise HTTPException(409,'Your answers changed. Review a new comparison and selection.')
    consent_event(record,value['insurer_consent_id'],'insurer_share')
    if value.get('broker_consent_id'):
        consent_event(record,value['broker_consent_id'],'broker_share')
    return value


class Selection(Strict):
    run_id: str
    expected_version: int
    plan_ids: list[str] = Field(min_length=1,max_length=3)
    insurer_consent_id: str
    broker_consent_id: str | None = None


@router.post('/selection')
def choose(body: Selection, record=Depends(owned), db: Session = Depends(session)):
    run=run_owned(db,record,body.run_id)
    if body.expected_version!=record.version or len(set(body.plan_ids))!=len(body.plan_ids):
        raise HTTPException(409,'Choose distinct plans from the current comparison')
    items=[i for i in run.data['result']['items'] if i['id'] in body.plan_ids]
    if len(items)!=len(body.plan_ids):
        raise HTTPException(422,'Choose only current eligible plans')
    insurer=consent_event(record,body.insurer_consent_id,'insurer_share')
    if set(insurer['recipients'])!={i['plan']['insurer_id'] for i in items}:
        raise HTTPException(422,'Consent must name exactly the selected fictional insurers')
    if body.broker_consent_id and consent_event(record,body.broker_consent_id,'broker_share')['recipients']!=['helm-demo-broker']:
        raise HTTPException(422,'Name the Helm demo broker in optional sharing consent')
    fingerprint=digest([body.run_id,record.version,sorted(body.plan_ids)])
    existing=record.data.get('wizard_selection')
    if existing and existing['run_id']==body.run_id:
        if existing['fingerprint']!=fingerprint:
            raise HTTPException(409,'This comparison already has a different reviewed selection. Generate a new comparison.')
        return selected(record)
    value={'reference':uid(),'run_id':body.run_id,'profile_version':record.version,'plan_ids':sorted(body.plan_ids),'insurer_consent_id':body.insurer_consent_id,'broker_consent_id':body.broker_consent_id,'fingerprint':fingerprint,'confirmed_at':now().isoformat(),'profile':run.data['result']['profile_snapshot'],'paid_pence':0,'policy_created':False,'account_linked':False,'notice':'Selection saved only. No payment, policy, account link or real insurer request was created.'}
    data=deepcopy(record.data)
    data['wizard_selection']=value
    save(db,record,data)
    return value


@router.get('/selection')
def selection(record=Depends(owned)):
    return selected(record)
