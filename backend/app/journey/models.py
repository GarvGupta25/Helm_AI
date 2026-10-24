from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..models import Base, now, uid
from ..research.storage import EncryptedState


class JourneySession(Base):
    __tablename__ = "journey_session"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    version: Mapped[int] = mapped_column(Integer, default=0)
    data: Mapped[dict] = mapped_column(EncryptedState(), default=dict)
    expires_at = mapped_column(DateTime(timezone=True))
    created_at = mapped_column(DateTime(timezone=True), default=now)


class ProfileVersion(Base):
    __tablename__ = "journey_profile_version"
    __table_args__ = (UniqueConstraint("session_id", "version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    session_id: Mapped[str] = mapped_column(ForeignKey("journey_session.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    data: Mapped[dict] = mapped_column(EncryptedState())
    created_at = mapped_column(DateTime(timezone=True), default=now)


class JourneyRun(Base):
    __tablename__ = "journey_run"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    session_id: Mapped[str] = mapped_column(ForeignKey("journey_session.id"), index=True)
    profile_version: Mapped[int] = mapped_column(Integer)
    data: Mapped[dict] = mapped_column(EncryptedState())
    created_at = mapped_column(DateTime(timezone=True), default=now)
