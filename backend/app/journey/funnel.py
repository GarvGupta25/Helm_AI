"""Opt-in daily counts only. No visitor identifiers, answers or event timestamps."""
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import Integer, String, delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from ..config import settings
from ..db import session
from ..models import Base, now
from ..public_assistant import _check_rate_limit
from .access import same_origin
from .schemas import Strict

router=APIRouter(prefix='/api/journey',tags=['optional anonymous counts'])
STEPS={'choice','consent','people','region','start-date','budget','excess','hospitals','benefits/hospital','benefits/wellbeing','benefits/everyday','ready','optional/existing-cover','optional/underwriting','optional/outpatient','optional/postcode','optional/conditions','review','plans','plan-detail','compare','selection','verify','verify/code','access','dashboard','broker'}


class FunnelCount(Base):
    __tablename__='journey_funnel_count'
    key: Mapped[str]=mapped_column(String(160),primary_key=True)
    day: Mapped[str]=mapped_column(String(10),index=True)
    event: Mapped[str]=mapped_column(String(32))
    step: Mapped[str]=mapped_column(String(40))
    mode: Mapped[str]=mapped_column(String(8))
    choice: Mapped[str]=mapped_column(String(12))
    count: Mapped[int]=mapped_column(Integer,default=0)


class Event(Strict):
    event: Literal['step_view','step_complete','mode_chosen','show_plans','plans_viewed','selection_complete','otp_started','otp_success','link_choice','dashboard_open','broker_requested']
    step: str
    mode: Literal['manual','chat',''] = ''
    choice: Literal['','24','48','checkpoint','optional','review'] = ''
    analytics_consent: Literal[True]


@router.post('/funnel',status_code=204)
def record(body:Event,request:Request,db:Session=Depends(session)):
    from fastapi import HTTPException
    same_origin(request)
    if body.step not in STEPS:
        raise HTTPException(422,'Unknown aggregate step')
    if not settings().journey_funnel_enabled:
        return Response(status_code=204)
    _check_rate_limit('funnel:'+body.event+':'+body.step+':'+request.client.host)
    day=now().date().isoformat()
    key=':'.join([day,body.event,body.step,body.mode,body.choice])
    row=db.scalar(select(FunnelCount).where(FunnelCount.key==key).with_for_update())
    if row:
        db.execute(update(FunnelCount).where(FunnelCount.key==key).values(count=FunnelCount.count+1))
    else:
        db.add(FunnelCount(key=key,day=day,event=body.event,step=body.step,mode=body.mode,choice=body.choice,count=1))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        db.execute(update(FunnelCount).where(FunnelCount.key==key).values(count=FunnelCount.count+1))
        db.commit()
    return Response(status_code=204)


def purge_counts(db,clock):
    db.execute(delete(FunnelCount).where(FunnelCount.day<(clock-timedelta(days=30)).date().isoformat()))
