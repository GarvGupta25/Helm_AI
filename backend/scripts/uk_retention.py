"""Explicit demo-only retention maintenance. Defaults to a read-only count."""
import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db import engine
from app.market.models import UKAudit, UKConsent, UKQuote, UKSupportTicket

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()
now = datetime.now(timezone.utc)
with Session(engine()) as db:
    expired = select(UKQuote.id).where(UKQuote.expires_at < now)
    print({"expired_quotes": db.scalar(select(func.count()).select_from(UKQuote).where(UKQuote.expires_at < now))})
    if args.apply:
        db.execute(delete(UKConsent).where(UKConsent.quote_id.in_(expired)))
        db.execute(delete(UKQuote).where(UKQuote.expires_at < now))
        db.execute(delete(UKSupportTicket).where(UKSupportTicket.created_at < now - timedelta(days=30)))
        db.execute(delete(UKAudit).where(UKAudit.timestamp < now - timedelta(days=30)))
        db.commit()
