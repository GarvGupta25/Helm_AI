"""Launch an isolated local test API; never connects to the user's configured database."""
import os
from pathlib import Path

root = Path(__file__).resolve().parents[2]
scratch = root / ".runtime"
scratch.mkdir(exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{(scratch / 'uk-e2e.db').as_posix()}"
os.environ["GROQ_API_KEY"] = ""

import uvicorn  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import engine  # noqa: E402
from app.market.seed import seed  # noqa: E402
from app.models import Base  # noqa: E402

Base.metadata.create_all(engine(), tables=[table for table in Base.metadata.tables.values() if table.name.startswith("uk_")])
with Session(engine()) as db:
    print(seed(db), flush=True)
uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
