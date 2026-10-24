"""Operator-only assignment in the isolated synthetic database; no public assignment API."""
import argparse
import os
from pathlib import Path
from uuid import UUID

root = Path(__file__).resolve().parents[2]
scratch = root/'.runtime'
os.environ['DATABASE_URL'] = f"sqlite:///{(scratch/'uk-e2e.db').as_posix()}"
os.environ['GROQ_API_KEY'] = ''
if not (scratch/'research-test.key').exists():
    raise SystemExit('Start the isolated demo API first.')
os.environ['RESEARCH_STATE_KEY'] = (scratch/'research-test.key').read_text().strip()

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import engine  # noqa: E402
from app.journey.broker import expected  # noqa: E402
from app.journey.case_models import Approval, Case, Document, Job  # noqa: E402
from app.journey.cases import active, audit, broker_notice, live_case  # noqa: E402

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-id', required=True, type=UUID)
    parser.add_argument('--broker-id', required=True, type=UUID, help='Existing Supabase user UUID with administrator-controlled broker role')
    parser.add_argument('--expected-version', required=True, type=int)
    args = parser.parse_args()
    with Session(engine()) as db:
        case = live_case(db.scalar(select(Case).where(Case.id == str(args.case_id)).with_for_update()))
        expected(case, args.expected_version)
        if not active(case, 'broker_share', ['helm-demo-broker']):
            raise SystemExit('Assignment requires current explicit broker-sharing consent.')
        for approval in db.scalars(select(Approval).join(Document).where(Document.case_id == case.id)):
            approval.revoked = True
        case.broker_id = str(args.broker_id)
        audit(case, 'administrator_demo_assignment', 'local_operator', broker_id=case.broker_id)
        if not db.scalar(select(Job.id).where(Job.dedupe_key == 'broker-case:'+case.id)):
            broker_notice(db, case)
        db.commit()
        print('Assigned synthetic case. Broker sign-in and role are still verified by Supabase on API access.')
