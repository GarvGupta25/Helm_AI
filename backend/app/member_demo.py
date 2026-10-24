"""Persistent member-only accounts for the explicitly isolated local prototype."""
import hashlib
import hmac
import re
from datetime import date, timedelta, timezone
from secrets import token_hex, token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, ForeignKey, String, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from .config import settings
from .db import session
from .journey.access import same_origin
from .journey.contact import keyed
from .models import Base, now, uid
from .public_assistant import _check_rate_limit
from .research.storage import EncryptedState, stable_key


class MemberAccount(Base):
    __tablename__ = 'member_demo_account'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email_hash: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(180))
    data: Mapped[dict] = mapped_column(EncryptedState())
    created_at = mapped_column(DateTime(timezone=True), default=now)


class MemberSession(Base):
    __tablename__ = 'member_demo_session'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    account_id: Mapped[str] = mapped_column(ForeignKey('member_demo_account.id'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at = mapped_column(DateTime(timezone=True))
    created_at = mapped_column(DateTime(timezone=True), default=now)


class MemberPolicy(Base):
    __tablename__ = 'member_demo_policy'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    account_id: Mapped[str] = mapped_column(ForeignKey('member_demo_account.id'), index=True)
    data: Mapped[dict] = mapped_column(EncryptedState())


def enabled():
    if not settings().member_demo_auth or settings().app_env not in {'development', 'test'}:
        raise HTTPException(404, 'Local member accounts are not enabled')
    if not stable_key():
        raise HTTPException(503, 'Configure a stable server encryption key before creating accounts')


def normalize(email):
    email = email.strip().casefold()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        raise HTTPException(422, 'Enter a valid email address')
    return email


def password_hash(password, salt=None):
    salt = salt or token_hex(16)
    result = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=32768, r=8, p=1, maxmem=64*1024*1024).hex()
    return salt+':'+result


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def open_session(db, account, request, response):
    token = token_urlsafe(32)
    for expired in db.scalars(select(MemberSession).where(MemberSession.expires_at <= now())):
        db.delete(expired)
    rows = db.scalars(select(MemberSession).where(MemberSession.account_id == account.id).order_by(MemberSession.created_at.desc())).all()
    for previous in rows[4:]:
        db.delete(previous)
    db.add(MemberSession(account_id=account.id, token_hash=token_hash(token), expires_at=now()+timedelta(hours=12)))
    db.commit()
    response.set_cookie('helm_member', token, httponly=True, secure=request.url.scheme == 'https', samesite='strict', max_age=43200, path='/api/member-demo')


def member(request: Request, db: Session = Depends(session)):
    enabled()
    token = request.cookies.get('helm_member', '')
    grant = db.scalar(select(MemberSession).where(MemberSession.token_hash == token_hash(token))) if len(token) == 43 else None
    if not grant or grant.expires_at.replace(tzinfo=timezone.utc) <= now():
        raise HTTPException(401, 'Sign in to your member account')
    account = db.get(MemberAccount, grant.account_id)
    if not account:
        raise HTTPException(401, 'Sign in again')
    return account


class Login(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class Register(Login):
    name: str = Field(min_length=1, max_length=100)


router = APIRouter(prefix='/api/member-demo', tags=['local prototype member accounts'])


@router.post('/register')
def register(body: Register, request: Request, response: Response, db: Session = Depends(session)):
    enabled()
    same_origin(request)
    _check_rate_limit('member-register:'+(request.client.host if request.client else 'unknown'))
    if len(body.password) < 12 or not body.name.strip():
        raise HTTPException(422, 'Enter your name and a password of at least 12 characters')
    email = normalize(body.email)
    account = MemberAccount(email_hash=keyed('member:'+email), password_hash=password_hash(body.password), data={'name': body.name.strip(), 'email': email, 'demo_fixture': False})
    db.add(account)
    try:
        db.flush()
        open_session(db, account, request, response)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'An account could not be created with those details. Try signing in.') from None
    return {'created': True, 'notice': 'Local prototype account created. No verification email is sent.'}


@router.post('/login')
def login(body: Login, request: Request, response: Response, db: Session = Depends(session)):
    enabled()
    same_origin(request)
    _check_rate_limit('member-login:'+(request.client.host if request.client else 'unknown'))
    account = db.scalar(select(MemberAccount).where(MemberAccount.email_hash == keyed('member:'+normalize(body.email))))
    stored = account.password_hash if account else '0'*32+':'+'0'*128
    actual = password_hash(body.password, stored.split(':')[0])
    if not account or not hmac.compare_digest(stored, actual):
        raise HTTPException(401, 'Email or password was not recognised')
    open_session(db, account, request, response)
    return {'signed_in': True}


@router.post('/logout')
def logout(request: Request, response: Response, account=Depends(member), db: Session = Depends(session)):
    same_origin(request)
    grant = db.scalar(select(MemberSession).where(MemberSession.account_id == account.id, MemberSession.token_hash == token_hash(request.cookies.get('helm_member', ''))))
    if grant:
        db.delete(grant)
    db.commit()
    response.delete_cookie('helm_member', path='/api/member-demo')
    return {'signed_out': True}


@router.get('/me')
def me(account=Depends(member), db: Session = Depends(session)):
    policies = db.scalars(select(MemberPolicy).where(MemberPolicy.account_id == account.id)).all()
    return {'name': account.data['name'], 'email': account.data['email'], 'has_policies': bool(policies),
            'policies': [{'id': p.id, **p.data} for p in policies], 'mode': 'local_synthetic_demo'}


DEMO_PASSWORD = 'HelmDemo!2026'


def seed_demo_members(db):
    enabled()
    created = 0
    for email, name, policy in [('new.member@example.test', 'Alex Morgan', False), ('policy.member@example.test', 'Jamie Taylor', True)]:
        if db.scalar(select(MemberAccount).where(MemberAccount.email_hash == keyed('member:'+email))):
            continue
        account = MemberAccount(email_hash=keyed('member:'+email), password_hash=password_hash(DEMO_PASSWORD), data={'name': name, 'email': email, 'demo_fixture': True})
        db.add(account)
        db.flush()
        if policy:
            today = date.today()
            db.add(MemberPolicy(account_id=account.id, data={'name': 'Helm Balanced', 'insurer': 'Harbour Demo Health', 'reference': 'HELM-DEMO-2026-001',
                'status': 'Synthetic active', 'monthly_pence': 8900, 'currency': 'GBP', 'start_date': today.isoformat(), 'renewal_date': (today+timedelta(days=365)).isoformat(),
                'excess_pence': 25000, 'hospital_list': 'Standard fictional list', 'benefits': ['Eligible inpatient treatment', 'Outpatient diagnostics up to £1,000/year', 'Referral and pre-authorisation required'],
                'exclusions': ['Pre-existing and chronic conditions are not established as covered', 'No emergency or routine pregnancy cover is assumed'], 'notice': 'Fictional policy for interface demonstration. No real insurance was purchased.'}))
        created += 1
    db.commit()
    return created
