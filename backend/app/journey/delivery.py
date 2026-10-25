"""Only reviewed notification templates, never AI drafts or arbitrary messages."""
import re
import smtplib
from email.message import EmailMessage
from urllib.parse import urlparse

import httpx

from ..config import settings
from .whatsmcp import WhatsMCPNotification


class ConsoleNotification:
    def send(self,contact,url):
        return {'delivery':'private_demo_inbox','external_sent':False,'template_status':'demo_only_not_provider_approved'}


class OfficialNotification:
    def send(self,contact,url):
        config=settings()
        destination=contact.data['destination']
        if destination not in config.otp_allowlist:
            raise ValueError('Notification recipient is not approved for this sandbox')
        parsed=urlparse(config.public_quote_origin)
        if parsed.scheme!='https' or not parsed.netloc or parsed.username or parsed.password or parsed.path not in {'','/'} or parsed.query or parsed.fragment:
            raise ValueError('Configure an HTTPS public quotation origin')
        absolute=config.public_quote_origin.rstrip('/')+(url if url.startswith('/my-quotes#') or url=='/broker.html' else '/my-quotes')
        if contact.channel=='whatsapp':
            if not (config.whatsapp_access_token and config.whatsapp_phone_number_id.isdigit() and re.fullmatch(r'v\d+\.\d+',config.whatsapp_graph_version) and config.whatsapp_utility_template):
                raise ValueError('Configure an approved WhatsApp utility template')
            payload={'messaging_product':'whatsapp','to':destination.lstrip('+'),'type':'template','template':{'name':config.whatsapp_utility_template,'language':{'code':config.whatsapp_template_language},'components':[{'type':'body','parameters':[{'type':'text','text':absolute}]}]}}
            with httpx.Client(timeout=8,follow_redirects=False) as client:
                response=client.post(f'https://graph.facebook.com/{config.whatsapp_graph_version}/{config.whatsapp_phone_number_id}/messages',headers={'Authorization':'Bearer '+config.whatsapp_access_token},json=payload)
                if response.status_code>=300 or not response.json().get('messages'):
                    raise ValueError('Provider did not accept the notification')
        else:
            if not (config.smtp_host and config.smtp_from and config.smtp_user and config.smtp_password):
                raise ValueError('Configure TLS SMTP for sandbox notifications')
            message=EmailMessage()
            message['Subject']='Your private Helm demo quotations'
            message['From']=config.smtp_from
            message['To']=destination
            message.set_content('A reviewed synthetic quotation update is available. No real cover is sold. Open your private dashboard: '+absolute)
            with smtplib.SMTP_SSL(config.smtp_host,config.smtp_port,timeout=8) as client:
                client.login(config.smtp_user,config.smtp_password)
                client.send_message(message)
        return {'delivery':'official_sandbox_provider','external_sent':True,'template_status':'operator_configured_not_independently_verified'}


def notification_provider(contact):
    mode=settings().otp_delivery_mode
    if mode=='whatsmcp' and contact.data.get('mode')==mode:
        return WhatsMCPNotification() if contact.channel=='whatsapp' else OfficialNotification()
    return OfficialNotification() if mode in {'whatsapp_sandbox','email_sandbox'} and contact.data.get('mode')==mode else ConsoleNotification()
