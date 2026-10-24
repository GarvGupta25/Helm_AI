"""Launch an isolated local test API; never connects to the user's configured database."""
import os
from pathlib import Path

root = Path(__file__).resolve().parents[2]
scratch = root / ".runtime"
scratch.mkdir(exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{(scratch / 'uk-e2e.db').as_posix()}"
os.environ["GROQ_API_KEY"] = ""

from cryptography.fernet import Fernet  # noqa: E402

research_key = scratch / "research-test.key"
if not research_key.exists():
    research_key.write_bytes(Fernet.generate_key())
os.environ["RESEARCH_STATE_KEY"] = research_key.read_text().strip()

import uvicorn  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import engine  # noqa: E402
from app.journey import case_models as journey_case_models  # noqa: E402, F401
from app.journey import models as journey_models  # noqa: E402, F401
from app.market.seed import seed  # noqa: E402
from app.models import Base  # noqa: E402
from app.research.generator import CONFIG, generate  # noqa: E402
from app.research.models import (  # noqa: E402
    ResearchRecord,  # noqa: E402
    ResearchSession,  # noqa: E402, F401
)

Base.metadata.create_all(engine(), tables=[table for table in Base.metadata.tables.values() if table.name.startswith(("uk_", "research_", "journey_"))])
with Session(engine()) as db:
    print(seed(db), flush=True)
    data = generate({**CONFIG, "profiles": 0, "histories": 0})
    for kind in ("insurers", "families", "variants", "clauses", "hospitals"):
        for item in data[kind]:
            db.merge(ResearchRecord(id=item["id"], kind=kind, version=CONFIG["version"], data=item))
    db.commit()
uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
