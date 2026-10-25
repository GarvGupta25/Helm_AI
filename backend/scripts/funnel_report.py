"""Operator-only aggregate JSON export; no public read endpoint or visitor join."""
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import engine
from app.journey.funnel import FunnelCount

with Session(engine()) as db:
    rows=db.scalars(select(FunnelCount).order_by(FunnelCount.day,FunnelCount.step,FunnelCount.event)).all()
    print(json.dumps([{'day':r.day,'event':r.event,'step':r.step,'mode':r.mode,'choice':r.choice,'count':r.count} for r in rows],indent=2))
