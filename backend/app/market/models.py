"""Additive records: no historical tables or monetary values are modified."""
from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..models import Base, now, uid


class UKQuote(Base):
    __tablename__ = "uk_quote_request"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    snapshot: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    receipt: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class UKConsent(Base):
    __tablename__ = "uk_consent_record"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    quote_id: Mapped[str] = mapped_column(String(64), index=True)
    purpose: Mapped[str] = mapped_column(String(100))
    text_version: Mapped[str] = mapped_column(String(30), default="uk-demo-1")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class UKAudit(Base):
    __tablename__ = "uk_chat_audit_event"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    intent: Mapped[str] = mapped_column(String(80))
    event: Mapped[dict] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class UKSupportTicket(Base):
    __tablename__ = "uk_support_ticket"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    reason: Mapped[str] = mapped_column(String(80))
    transcript_ref: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
