"""Separate research snapshots; no relationship to real customer/policy tables."""
from datetime import datetime, timezone
from secrets import token_urlsafe

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from ..models import Base


class ResearchRecord(Base):
    __tablename__ = "research_record"
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    version: Mapped[str] = mapped_column(String(60))
    data: Mapped[dict] = mapped_column(JSON)


class ResearchSession(Base):
    __tablename__ = "research_session"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: token_urlsafe(32))
    data: Mapped[dict] = mapped_column(JSON)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
