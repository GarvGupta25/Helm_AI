from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..models import Base, now, uid
from ..research.storage import EncryptedState


class Contact(Base):
    __tablename__ = "journey_contact"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    session_id: Mapped[str] = mapped_column(ForeignKey("journey_session.id"), index=True)
    channel: Mapped[str] = mapped_column(String(16))
    lookup_hash: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(EncryptedState())
    verified_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=now)


class Case(Base):
    __tablename__ = "journey_case"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    session_id: Mapped[str] = mapped_column(ForeignKey("journey_session.id"), index=True)
    contact_id: Mapped[str | None] = mapped_column(ForeignKey("journey_contact.id"), nullable=True)
    request_key: Mapped[str] = mapped_column(String(64), unique=True)
    broker_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="new", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    data: Mapped[dict] = mapped_column(EncryptedState())
    expires_at = mapped_column(DateTime(timezone=True))
    created_at = mapped_column(DateTime(timezone=True), default=now)
    __mapper_args__ = {"version_id_col": version}


class QuoteRequest(Base):
    __tablename__ = "journey_quote_request"
    __table_args__ = (UniqueConstraint("case_id", "insurer_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey("journey_case.id"), index=True)
    insurer_id: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(24), default="queued")
    data: Mapped[dict] = mapped_column(EncryptedState())
    due_at = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)


class Document(Base):
    __tablename__ = "journey_document"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey("journey_case.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    content_hash: Mapped[str] = mapped_column(String(64))
    ai_drafted: Mapped[bool] = mapped_column(Boolean, default=False)
    data: Mapped[dict] = mapped_column(EncryptedState())
    created_at = mapped_column(DateTime(timezone=True), default=now)


class Quotation(Base):
    __tablename__ = "journey_quotation"
    __table_args__ = (UniqueConstraint("request_id", "plan_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    request_id: Mapped[str] = mapped_column(ForeignKey("journey_quote_request.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("journey_document.id"))
    plan_id: Mapped[str] = mapped_column(String(180))
    data: Mapped[dict] = mapped_column(EncryptedState())
    expires_at = mapped_column(DateTime(timezone=True))
    created_at = mapped_column(DateTime(timezone=True), default=now)


class Approval(Base):
    __tablename__ = "journey_approval"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    document_id: Mapped[str] = mapped_column(ForeignKey("journey_document.id"), index=True)
    content_hash: Mapped[str] = mapped_column(String(64))
    scope_hash: Mapped[str] = mapped_column(String(64))
    approved_by: Mapped[str] = mapped_column(String(36))
    decision: Mapped[str] = mapped_column(String(16))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at = mapped_column(DateTime(timezone=True), default=now)


class Job(Base):
    __tablename__ = "journey_delivery_job"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    case_id: Mapped[str | None] = mapped_column(ForeignKey("journey_case.id"), nullable=True, index=True)
    contact_id: Mapped[str | None] = mapped_column(ForeignKey("journey_contact.id"), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(32))
    dedupe_key: Mapped[str] = mapped_column(String(160), unique=True)
    status: Mapped[str] = mapped_column(String(24), default="queued")
    data: Mapped[dict] = mapped_column(EncryptedState())
    due_at = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at = mapped_column(DateTime(timezone=True), default=now)


class Grant(Base):
    __tablename__ = "journey_access_grant"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    case_id: Mapped[str | None] = mapped_column(ForeignKey("journey_case.id"), nullable=True, index=True)
    contact_id: Mapped[str] = mapped_column(ForeignKey("journey_contact.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    kind: Mapped[str] = mapped_column(String(24))
    data: Mapped[dict] = mapped_column(EncryptedState(), default=dict)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at = mapped_column(DateTime(timezone=True))


MODELS = (Contact, Case, QuoteRequest, Document, Quotation, Approval, Job, Grant)
