"""Reviewed notifications: private demo inbox or explicitly configured sandbox."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from ..models import now
from .case_models import Case, Contact, Grant, Job
from .cases import active
from .delivery import notification_provider


def quiet_until(preferences, clock):
    local = clock.astimezone(ZoneInfo(preferences['time_zone']))
    start, end = preferences['quiet_start'], preferences['quiet_end']
    quiet = start != end and (start <= local.hour < end if start < end else local.hour >= start or local.hour < end)
    if not quiet:
        return None
    finish = local.replace(hour=end, minute=0, second=0, microsecond=0)
    if finish <= local:
        finish += timedelta(days=1)
    return finish.astimezone(timezone.utc)


def process_notifications(db, clock=None):
    clock = clock or now()
    count = 0
    for job in db.scalars(select(Job).where(Job.status == 'queued', Job.kind.in_(['quote_update', 'link_reminder','access_link_notify']), Job.due_at <= clock).with_for_update(skip_locked=True)):
        case = db.scalar(select(Case).where(Case.id == job.case_id).with_for_update())
        contact = db.get(Contact, job.contact_id)
        if (not case or case.status == 'closed' or case.data.get('withdrawn') or case.expires_at.replace(tzinfo=timezone.utc) <= clock
                or not contact or not contact.verified_at or not active(case, 'notify_'+contact.channel, [contact.id])
                or contact.channel not in case.data['preferences']['channels']
                or not (active(case, 'insurer_share') or active(case, 'broker_share'))):
            job.status = 'cancelled'
            continue
        if job.kind == 'link_reminder':
            grant = db.get(Grant, job.data['grant_id'])
            if not grant or grant.revoked or grant.used or grant.expires_at.replace(tzinfo=timezone.utc) <= clock:
                job.status = 'cancelled'
                continue
        quiet = quiet_until(case.data['preferences'], clock)
        if quiet:
            job.due_at = quiet
            continue
        try:
            delivered=notification_provider(contact).send(contact,job.data.get('url','/my-quotes'))
            job.data={**job.data,'channel':contact.channel,**delivered}
            job.status='delivered_sandbox' if delivered['external_sent'] else 'delivered_demo'
        except Exception:
            job.data={**job.data,'delivery':'failed','external_sent':False,'notice':'Configured sandbox delivery failed; use the private dashboard.'}
            job.status='failed'
        job.attempts += 1
        count += 1
    # Verification codes are short lived even when nobody reads the inbox again.
    for job in db.scalars(select(Job).where(Job.kind == 'verification')):
        if job.data.get('code') and datetime.fromisoformat(job.data['expires_at']) <= clock:
            job.data = {'notice': 'Verification expired'}
            job.status = 'expired'
    db.commit()
    return count
