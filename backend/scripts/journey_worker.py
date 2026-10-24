"""Run the isolated synthetic journey worker. No external delivery adapters exist."""
import argparse
import os
import time
from pathlib import Path

root = Path(__file__).resolve().parents[2]
scratch = root / ".runtime"
scratch.mkdir(exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{(scratch / 'uk-e2e.db').as_posix()}"
os.environ["GROQ_API_KEY"] = ""
if not (scratch / "research-test.key").exists():
    raise SystemExit("Start the isolated demo API first to initialize its local key and tables.")
os.environ["RESEARCH_STATE_KEY"] = (scratch / "research-test.key").read_text().strip()

from sqlalchemy.orm import Session  # noqa: E402

from app.db import engine  # noqa: E402
from app.journey.worker import process_quotes  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    while True:
        with Session(engine()) as db:
            print({"synthetic_requests_processed": process_quotes(db)}, flush=True)
        if args.once:
            break
        time.sleep(2)
