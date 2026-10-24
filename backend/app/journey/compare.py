from copy import deepcopy
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import session
from ..public_assistant import _check_rate_limit
from ..research.router import catalogue
from .models import JourneyRun
from .recommendations import compute
from .router import digest, owned, save
from .schemas import JourneyProfile, Strict

router = APIRouter(prefix="/api/journey", tags=["journey comparison"])


def current_catalogue(db):
    return sorted(catalogue(db), key=lambda plan: plan['id'])


def run_owned(db, record, ident, current=True):
    run = db.scalar(select(JourneyRun).where(JourneyRun.id == ident, JourneyRun.session_id == record.id))
    if not run:
        raise HTTPException(404, "Comparison unavailable in this session")
    if current and run.profile_version != record.version:
        raise HTTPException(409, "Your needs changed. Generate a new comparison first.")
    return run


@router.post("/recommendations")
def recommendations(limit: int = Query(default=3,ge=1,le=10), record=Depends(owned), db: Session = Depends(session)):
    _check_rate_limit('journey-compute:'+record.id)
    if not record.version:
        raise HTTPException(422, "Confirm your intake answers first")
    profile = JourneyProfile.model_validate(record.data["confirmed"])
    try:
        result = compute(current_catalogue(db), profile, limit=limit)
    except ValueError as error:
        raise HTTPException(422, str(error)) from None
    rows = db.scalars(select(JourneyRun).where(JourneyRun.session_id == record.id).order_by(JourneyRun.created_at)).all()
    for row in rows[:-4]:
        db.delete(row)
    row = JourneyRun(session_id=record.id, profile_version=record.version, data={"result": result, "catalogue_hash": digest(current_catalogue(db))})
    db.add(row)
    db.flush()
    data = deepcopy(record.data)
    data["latest_run"] = row.id
    data["shortlist"] = []
    save(db, record, data)
    return {**result, "run_id": row.id, "profile_version": row.profile_version}


class ViewFilters(Strict):
    budget_max: int | None = Field(default=None,ge=0,le=1000000)
    excess_max: int | None = Field(default=None,ge=0,le=50000)
    hospital_min: int | None = Field(default=None,ge=1,le=2)
    benefits: list[str] = Field(default_factory=list,max_length=11)
    preferred: list[str] = Field(default_factory=list,max_length=11)
    underwriting: Literal['moratorium','full_medical'] | None = None
    outpatient_min: int | None = Field(default=None,ge=0,le=10000000)
    sort: Literal['best_match','premium','excess','cover'] = 'best_match'


def filter_view(items, filters):
    from ..research.generator import CARE
    if (set(filters.benefits)|set(filters.preferred))-set(CARE):
        raise HTTPException(422,'Choose supported benefits')
    shown = [item for item in items
        if (filters.budget_max is None or item['quote']['monthly_pence'] <= filters.budget_max)
        and (filters.excess_max is None or item['plan']['excess_pence'] <= filters.excess_max)
        and (filters.hospital_min is None or item['plan']['network'] >= filters.hospital_min)
        and all((item['plan'].get('pre_existing') == 'covered' if benefit=='pre_existing' else item['plan']['limits'].get(benefit,0)>0) for benefit in filters.benefits)
        and (filters.underwriting is None or item['plan']['underwriting'] == filters.underwriting)
        and (filters.outpatient_min is None or item['plan']['limits']['outpatient'] >= filters.outpatient_min)]
    keys = {'premium':lambda i:(i['quote']['monthly_pence'],i['id']), 'excess':lambda i:(i['plan']['excess_pence'],i['id']), 'cover':lambda i:(-i['standard']['components']['coverage'],i['id'])}
    if filters.sort in keys:
        return sorted(shown,key=keys[filters.sort])
    return sorted(shown,key=lambda i:-sum(i['plan']['limits'].get(benefit,0)>0 for benefit in filters.preferred)) if filters.preferred else shown


@router.post('/runs/{run_id}/view')
def view(run_id: str, body: ViewFilters, record=Depends(owned), db: Session = Depends(session)):
    row = run_owned(db,record,run_id)
    shown = filter_view(row.data['result']['items'],body)
    return {'items':shown,'count':len(shown),'profile_unchanged':True,'profile_version':record.version}


class Compared(Strict):
    plan_ids: list[str] = Field(min_length=2,max_length=3)


@router.post('/runs/{run_id}/comparison')
def comparison(run_id: str, body: Compared, record=Depends(owned), db: Session = Depends(session)):
    from .explanations import main_differences
    row=run_owned(db,record,run_id)
    items=[item for item in row.data['result']['items'] if item['id'] in body.plan_ids]
    if len(items)!=len(body.plan_ids) or len(set(body.plan_ids))!=len(body.plan_ids):
        raise HTTPException(422,'Compare two or three distinct current plans')
    return {'main_differences':main_differences(items),'sources':[item['id'] for item in items],'profile_version':record.version}


@router.get("/runs/{run_id}")
def get_run(run_id: str, record=Depends(owned), db: Session = Depends(session)):
    row = run_owned(db, record, run_id)
    return {**row.data["result"], "run_id": row.id, "profile_version": row.profile_version}


class Selection(Strict):
    run_id: str
    expected_version: int
    plan_ids: list[str]


@router.put("/shortlist")
def shortlist(body: Selection, record=Depends(owned), db: Session = Depends(session)):
    row = run_owned(db, record, body.run_id)
    if body.expected_version != record.version or len(body.plan_ids) != len(set(body.plan_ids)) or len(body.plan_ids) > 3:
        raise HTTPException(422, "Choose up to three distinct plans from the current comparison")
    if not set(body.plan_ids) <= {item["id"] for item in row.data["result"]["items"]}:
        raise HTTPException(422, "Select plans from the confirmed shortlist, not a what-if preview")
    data = deepcopy(record.data)
    data["shortlist"] = {"run_id": row.id, "plan_ids": body.plan_ids, "profile_version": record.version}
    save(db, record, data)
    return data["shortlist"]


@router.post("/runs/{run_id}/what-if")
def what_if(run_id: str, body: JourneyProfile, record=Depends(owned), db: Session = Depends(session)):
    _check_rate_limit('journey-compute:'+record.id)
    from .router import check_sensitive
    check_sensitive(body, record)
    row = run_owned(db, record, run_id)
    if digest(current_catalogue(db)) != row.data["catalogue_hash"]:
        raise HTTPException(409, "Catalogue changed; create a new comparison")
    try:
        result = compute(current_catalogue(db), body)
    except ValueError as error:
        raise HTTPException(422, str(error)) from None
    return {"hypothetical": True, "profile_unchanged": True, "result": result}
