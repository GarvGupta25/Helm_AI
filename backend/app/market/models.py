"""Additive records: no historical tables or monetary values are modified."""
from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Integer, String, Text, UniqueConstraint
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


class UKPlan(Base):
    __tablename__ = "uk_plan"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    provider: Mapped[str] = mapped_column(String(100))
    tier: Mapped[str] = mapped_column(String(40))
    hospital_list: Mapped[str] = mapped_column(String(40))
    version: Mapped[str] = mapped_column(String(40))
    key_facts: Mapped[dict] = mapped_column(JSON)
    demo: Mapped[bool] = mapped_column(Boolean, default=True)


class UKPremium(Base):
    __tablename__ = "uk_premium_table"
    __table_args__ = (
        UniqueConstraint("plan_id", "age_band", "region", "smoker", "excess_pence"),
        CheckConstraint("base_monthly_pence >= 0"),
        CheckConstraint("excess_pence >= 0"),
    )
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(40), index=True)
    age_band: Mapped[str] = mapped_column(String(20))
    region: Mapped[str] = mapped_column(String(40))
    smoker: Mapped[bool] = mapped_column(Boolean)
    excess_pence: Mapped[int] = mapped_column(Integer)
    base_monthly_pence: Mapped[int] = mapped_column(Integer)


class UKUnderwritingOption(Base):
    __tablename__ = "uk_underwriting_option"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    description: Mapped[str] = mapped_column(Text)


class UKParty(Base):
    """Reserved for a future encrypted/authenticated account-linking migration."""
    __tablename__ = "uk_party"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    account_id: Mapped[str] = mapped_column(String(36), index=True)
    encrypted_details: Mapped[str] = mapped_column(Text)


class UKComplianceFlag(Base):
    __tablename__ = "uk_compliance_flag"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    code: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), default="unresolved")
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
