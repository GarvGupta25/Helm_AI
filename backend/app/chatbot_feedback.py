"""Chatbot-only feedback store. No chat history or account credentials are collected."""
import hashlib
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, String, UniqueConstraint, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from .config import settings
from .models import now, uid
from .public_assistant import _check_rate_limit
from .research.storage import EncryptedState, stable_key


class FeedbackBase(DeclarativeBase):
    pass


class ChatFeedback(FeedbackBase):
    __tablename__ = 'chatbot_feedback'
    __table_args__ = (UniqueConstraint('session_hash', 'message_id', 'kind'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    session_hash: Mapped[str] = mapped_column(String(64))
    message_id: Mapped[str] = mapped_column(String(36))
    kind: Mapped[str] = mapped_column(String(16))
    rating: Mapped[str | None] = mapped_column(String(8), nullable=True)
    category: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(16), default='new')
    data: Mapped[dict] = mapped_column(EncryptedState())
    created_at = mapped_column(DateTime(timezone=True), default=now)
    updated_at = mapped_column(DateTime(timezone=True), default=now)


@lru_cache
def feedback_engine(url):
    engine = create_engine(url, pool_pre_ping=True)
    FeedbackBase.metadata.create_all(engine)
    return engine


def feedback_db():
    config = settings()
    url = config.chatbot_feedback_database_url
    if not url:
        path = Path(__file__).resolve().parents[2]/'.runtime'/'chatbot-feedback.db'
        path.parent.mkdir(exist_ok=True)
        url = 'sqlite:///'+path.as_posix()
    if url == config.database_url:
        raise HTTPException(503, 'Configure a separate chatbot feedback database')
    if not stable_key():
        raise HTTPException(503, 'Configure the server feedback encryption key before saving feedback')
    with Session(feedback_engine(url)) as db:
        yield db


class Feedback(BaseModel):
    model_config = ConfigDict(extra='forbid')
    session_id: UUID
    message_id: UUID
    kind: Literal['feedback', 'issue'] = 'feedback'
    rating: Literal['up', 'down'] | None = None
    category: Literal['general', 'incorrect', 'unclear', 'unsafe', 'technical', 'other'] = 'general'
    comment: str = Field(default='', max_length=1500)
    include_answer: bool = False
    answer_excerpt: str = Field(default='', max_length=6000)


router = APIRouter(prefix='/api/public/assistant', tags=['chatbot feedback'])


@router.post('/feedback')
def record_feedback(body: Feedback, request: Request, db: Session = Depends(feedback_db)):
    _check_rate_limit('feedback:'+(request.client.host if request.client else 'unknown'))
    if (body.kind == 'feedback' and not body.rating) or (body.kind == 'issue' and not body.comment.strip()):
        raise HTTPException(422, 'Choose a rating, or describe the issue')
    session_hash = hashlib.sha256(str(body.session_id).encode()).hexdigest()
    query = select(ChatFeedback).where(ChatFeedback.session_hash == session_hash, ChatFeedback.message_id == str(body.message_id), ChatFeedback.kind == body.kind)
    row = db.scalar(query.with_for_update())
    data = dict(row.data) if row else {'comment': '', 'answer_excerpt': '', 'answer_shared': False}
    if 'comment' in body.model_fields_set:
        data['comment'] = body.comment.strip()
    if 'include_answer' in body.model_fields_set:
        data.update(answer_excerpt=body.answer_excerpt if body.include_answer else '', answer_shared=body.include_answer)
    if not row:
        row = ChatFeedback(session_hash=session_hash, message_id=str(body.message_id), kind=body.kind, data=data, category=body.category)
        db.add(row)
    row.rating, row.data, row.updated_at = body.rating, data, now()
    if 'category' in body.model_fields_set:
        row.category = body.category
    # Submitted feedback has its own 90-day retention; ordinary chat stays session-only.
    purge_feedback(db)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Feedback changed in another request. Please try again.') from None
    return {'recorded': True, 'reference': row.id, 'notice': 'Saved to the separate chatbot feedback store. No conversation history was saved.'}


def purge_feedback(db):
    rows = db.scalars(select(ChatFeedback).where(ChatFeedback.updated_at < now()-timedelta(days=90)).limit(100)).all()
    for expired in rows:
        db.delete(expired)
    return len(rows)
