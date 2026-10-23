"""Explicit local/admin import and retention; never a public catalogue-writing API."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db import engine
from app.research.generator import validate
from app.research.models import ResearchRecord, ResearchSession


def ingest(db, folder):
    data = {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in folder.glob("*.json") if path.stem != "quality"}
    report = validate(data)
    for kind in ("insurers", "families", "variants", "clauses", "hospitals"):
        for item in data[kind]:
            existing = db.get(ResearchRecord, item["id"])
            if existing and (existing.version != data["lineage"]["version"] or existing.data != item):
                raise ValueError("Catalogue snapshots are immutable. Use a new catalogue database/version namespace.")
            db.merge(ResearchRecord(id=item["id"], kind=kind, version=data["lineage"]["version"], data=item))
    db.commit()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--import-dir", type=Path)
    parser.add_argument("--create-demo-tables", action="store_true")
    parser.add_argument("--purge-expired", action="store_true")
    args = parser.parse_args()
    if args.create_demo_tables:
        ResearchRecord.__table__.create(engine(), checkfirst=True)
        ResearchSession.__table__.create(engine(), checkfirst=True)
    with Session(engine()) as db:
        if args.import_dir:
            print(json.dumps(ingest(db, args.import_dir)))
        if args.purge_expired:
            result = db.execute(delete(ResearchSession).where(ResearchSession.expires_at <= datetime.now(timezone.utc)))
            db.commit()
            print(f"Expired research sessions deleted: {result.rowcount}")
