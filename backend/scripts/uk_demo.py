"""Explicit demo database setup; no automatic production migration."""
import argparse

from sqlalchemy.orm import Session

from app.db import engine
from app.market import models  # noqa: F401
from app.market.seed import seed
from app.models import Base

parser = argparse.ArgumentParser()
parser.add_argument("--create-demo-tables", action="store_true")
args = parser.parse_args()
if args.create_demo_tables:
    Base.metadata.create_all(engine())
with Session(engine()) as db:
    print(seed(db))
