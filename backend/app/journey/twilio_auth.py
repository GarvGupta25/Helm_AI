"""Opt-in Twilio transports. No implicit provider fallback or automatic secret retries."""
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from twilio.http.http_client import TwilioHttpClient
from twilio.request_validator import RequestValidator
from twilio.rest import Client

from ..config import settings
from ..db import session
from ..models import now
from .case_models import Contact, Job, OtpWindow
from .contact import keyed

router = APIRouter(prefix='/api/journey/webhooks/twilio', tags=['Twilio callbacks'])
AUTH_MODES = {'twilio', 'mock'}


def mock_enabled():
    c = settings()
    return c.otp_delivery_mode == 'mock' and c.whatsapp_mock_auth and c.app_env in {'development', 'test'}


def valid_origin(value, local=False):
    p = urlparse(value)
    return bool(p.hostname and not p.username and not p.password and p.path in {'', '/'} and not p.query
                and not p.fragment and (p.scheme == 'https' or
                (local and p.scheme == 'http' and p.hostname in {'localhost', '127.0.0.1', '::1'})))


def ready():
    c = settings()
    return bool(re.fullmatch(r'AC[0-9a-fA-F]{32}', c.twilio_account_sid) and c.twilio_auth_token
                and re.fullmatch(r'whatsapp:\+[1-9]\d{7,14}', c.twilio_whatsapp_from)
                and valid_origin(c.public_quote_origin)
                and valid_origin(c.twilio_webhook_origin)
                and 1 <= c.magic_link_expiry_minutes <= 10
                and ((c.twilio_otp_provider == 'twilio_verify' and
                      re.fullmatch(r'VA[0-9a-fA-F]{32}', c.twilio_verify_service_sid)) or
                     (c.twilio_otp_provider == 'custom' and
                      re.fullmatch(r'HX[0-9a-fA-F]{32}', c.twilio_otp_content_sid)))
                and (not c.twilio_magic_link_content_sid or re.fullmatch(r'HX[0-9a-fA-F]{32}', c.twilio_magic_link_content_sid))
                and (c.app_env in {'development', 'test'} or
                     (not c.twilio_sandbox and c.twilio_magic_link_content_sid)))


def validate_startup():
    c = settings()
    if c.otp_delivery_mode == 'mock' and not mock_enabled():
        raise RuntimeError('Mock authentication requires explicit isolated development/test configuration')
    if c.otp_delivery_mode in AUTH_MODES and not 1 <= c.magic_link_expiry_minutes <= 10:
        raise RuntimeError('Authentication links must expire within one to ten minutes')
    if c.otp_delivery_mode == 'twilio' and not ready():
        raise RuntimeError('Twilio authentication configuration is incomplete or unsafe; see WHATSAPP_AUTH_SETUP.md')


def client():
    c = settings()
    if not ready():
        raise ValueError('Twilio is not configured')
    return Client(c.twilio_account_sid, c.twilio_auth_token,
                  http_client=TwilioHttpClient(timeout=8, max_retries=0))


def safe_failure():
    return HTTPException(503, 'WhatsApp provider unavailable. Check the Console recipient, template and delivery logs before retrying.')


def callback(path):
    return settings().twilio_webhook_origin.rstrip('/') + '/api/journey/webhooks/twilio/' + path


class TwilioOtp:
    def send(self, destination, code, contact_id):
        c = settings()
        try:
            if c.twilio_otp_provider == 'twilio_verify':
                result = client().verify.v2.services(c.twilio_verify_service_sid).verifications.create(
                    to=destination, channel='whatsapp')
                if result.status != 'pending':
                    raise ValueError('Verification not pending')
                return {'provider_status': 'queued', 'verification_sid': result.sid, 'otp_provider': 'twilio_verify'}
            result = client().messages.create(to='whatsapp:' + destination, from_=c.twilio_whatsapp_from,
                content_sid=c.twilio_otp_content_sid, content_variables=json.dumps({'1': 'Helm AI', '2': code}),
                status_callback=callback('status'))
            return {'provider_status': 'queued', 'message_sid': result.sid, 'otp_provider': 'custom'}
        except Exception:
            raise safe_failure() from None


def check_managed(db, contact, code):
    data = dict(contact.data)
    if data.get('consumed') or datetime.fromisoformat(data['expires_at']) <= now():
        raise HTTPException(410, 'Verification expired or already used; request a new code')
    if data.get('attempts', 0) >= 5:
        raise HTTPException(429, 'Verification attempt limit reached')
    data['attempts'] = data.get('attempts', 0) + 1
    contact.data = data
    # Keep the contact lock through checking; persist failures even during provider outages.
    db.flush()
    try:
        result = client().verify.v2.services(settings().twilio_verify_service_sid).verification_checks.create(
            verification_sid=data['verification_sid'], code=code)
        approved = result.status == 'approved' and result.to == data['destination']
    except Exception:
        db.commit()
        raise safe_failure() from None
    if not approved:
        db.commit()
        raise HTTPException(422, 'Code could not be verified')
    contact.verified_at = now()
    contact.data = {**data, 'consumed': True}


def active_window(db, destination):
    row = db.get(OtpWindow, keyed('twilio-inbound:' + destination))
    return bool(row and row.expires_at.replace(tzinfo=timezone.utc) > now())


def send_link(db, contact, path):
    c = settings()
    if not contact.verified_at or contact.data.get('mode') != 'twilio':
        raise HTTPException(403, 'Verify this WhatsApp contact first')
    if contact.data['destination'] not in c.otp_allowlist:
        raise HTTPException(403, 'Recipient is not enabled')
    if not re.fullmatch(r'/my-quotes#[A-Za-z0-9_-]{43}', path):
        raise ValueError('Invalid private link')
    url = c.public_quote_origin.rstrip('/') + path
    args = {'to': 'whatsapp:' + contact.data['destination'], 'from_': c.twilio_whatsapp_from,
            'status_callback': callback('status')}
    if not c.twilio_sandbox and re.fullmatch(r'HX[0-9a-fA-F]{32}', c.twilio_magic_link_content_sid):
        args.update(content_sid=c.twilio_magic_link_content_sid, content_variables=json.dumps({'1': url}))
    elif c.twilio_sandbox and c.twilio_legacy_session_messages and active_window(db, contact.data['destination']):
        args['body'] = (f'Your WhatsApp number is verified. Continue to your private Helm quotations: {url} '
                        f'This single-use link expires in {c.magic_link_expiry_minutes} minutes. Do not share it.')
    else:
        return {'provider_status': 'blocked', 'external_sent': False,
                'notice': 'Trial restrictions prevent link delivery. Use isolated mock mode, or an approved production template. Legacy Sandbox requires a verified inbound session and explicit operator configuration.'}
    try:
        result = client().messages.create(**args)
        return {'provider_status': 'accepted', 'message_sid': result.sid, 'external_sent': True,
                'notice': 'The provider accepted your link. Delivery to your phone is not yet confirmed.'}
    except Exception:
        return {'provider_status': 'failed', 'external_sent': False,
                'notice': 'Link delivery could not be confirmed. Check provider logs before reverifying.'}


async def signed_form(request, path):
    c = settings()
    if c.otp_delivery_mode != 'twilio' or not ready():
        raise HTTPException(404, 'Callback unavailable')
    body = await request.body()
    if len(body) > 16384 or request.url.query:
        raise HTTPException(400, 'Invalid callback')
    form = await request.form()
    if not RequestValidator(c.twilio_auth_token).validate(callback(path), form,
                                                        request.headers.get('X-Twilio-Signature', '')):
        raise HTTPException(403, 'Invalid callback signature')
    if form.get('AccountSid') != c.twilio_account_sid:
        raise HTTPException(403, 'Invalid callback account')
    return form


@router.post('/inbound')
async def inbound(request: Request, db: Session = Depends(session)):
    form = await signed_form(request, 'inbound')
    sender = str(form.get('From', ''))
    if form.get('To') != settings().twilio_whatsapp_from or not sender.startswith('whatsapp:+'):
        raise HTTPException(403, 'Invalid callback recipient')
    destination = sender.removeprefix('whatsapp:')
    if destination not in settings().otp_allowlist:
        return Response(status_code=204)
    # Timestamp the provider's message, not webhook receipt: replay cannot extend the window.
    try:
        message = client().messages(str(form.get('MessageSid', ''))).fetch()
        if message.direction != 'inbound' or message.from_ != sender or message.to != form.get('To'):
            raise ValueError('Invalid message')
        expiry = message.date_created + timedelta(hours=24)
    except Exception:
        raise safe_failure() from None
    if expiry > now():
        db.merge(OtpWindow(key=keyed('twilio-inbound:' + destination), data={}, expires_at=expiry))
        db.commit()
    return Response(status_code=204)


@router.post('/status')
async def message_status(request: Request, db: Session = Depends(session)):
    form = await signed_form(request, 'status')
    sid, status = str(form.get('MessageSid', '')), str(form.get('MessageStatus', ''))
    order = {'accepted': 0, 'queued': 1, 'sending': 2, 'sent': 3, 'delivered': 4, 'read': 5,
             'failed': 6, 'undelivered': 6}
    if not re.fullmatch(r'SM[0-9a-fA-F]{32}', sid) or status not in order:
        raise HTTPException(400, 'Invalid message status')
    # State is encrypted: use bounded recent records, never an unbounded PII scan.
    for model in (Contact, Job):
        for row in db.scalars(select(model).where(model.created_at > now()-timedelta(days=1)).with_for_update()):
            if row.data.get('message_sid') == sid:
                old = row.data.get('provider_status', 'accepted')
                if order[status] >= order.get(old, 0):
                    row.data = {**row.data, 'provider_status': status, 'error_code': str(form.get('ErrorCode', ''))[:12]}
    db.commit()
    return Response(status_code=204)
