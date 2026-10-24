"""Run the isolated synthetic worker; default delivery stays in the demo inbox."""
import argparse
import os
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[2]
scratch = root / ".runtime"
scratch.mkdir(exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{(scratch / 'uk-e2e.db').as_posix()}"
os.environ["GROQ_API_KEY"] = ""
if '--allow-configured-sandbox' not in sys.argv:
    os.environ['OTP_DELIVERY_MODE'] = 'console'
if not (scratch / "research-test.key").exists():
    raise SystemExit("Start the isolated demo API first to initialize its local key and tables.")
os.environ["RESEARCH_STATE_KEY"] = (scratch / "research-test.key").read_text().strip()

from sqlalchemy.orm import Session  # noqa: E402

from app.chatbot_feedback import feedback_db, purge_feedback  # noqa: E402
from app.db import engine  # noqa: E402
from app.journey.notifications import process_notifications  # noqa: E402
from app.journey.retention import purge_expired  # noqa: E402
from app.journey.worker import process_quotes  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument('--allow-configured-sandbox',action='store_true',help='Use explicitly configured, allow-listed notification transports')
    args = parser.parse_args()
    feedback_cleanup_at = 0
    while True:
        with Session(engine()) as db:
            print({"synthetic_requests_processed": process_quotes(db), "demo_notifications_processed": process_notifications(db), "expired_cases_purged": purge_expired(db)}, flush=True)
        if time.monotonic() >= feedback_cleanup_at:
            for feedback_store in feedback_db():
                purge_feedback(feedback_store)
                feedback_store.commit()
            feedback_cleanup_at = time.monotonic()+600
        if args.once:
            break
        time.sleep(2)
