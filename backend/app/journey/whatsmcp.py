"""WhatsMCP REST transport shared by OTP and reviewed private-link delivery."""
import re
from urllib.parse import urlparse

import httpx

from ..config import settings


class WhatsMCPError(Exception):
    def __init__(self,notice,status_code=503):
        super().__init__(notice)
        self.status_code=status_code


def configured():
    config=settings()
    return bool(config.whatsmcp_api_key.strip() and re.fullmatch(r'[A-Za-z0-9_-]{1,80}',config.whatsmcp_account_id))


def send_message(destination,text,template='',variables=None):
    config=settings()
    if not configured():
        raise WhatsMCPError('Add the WhatsMCP API key and linked sender account ID to the server configuration.')
    if destination not in config.otp_allowlist:
        raise WhatsMCPError('This WhatsApp recipient is not in the approved test list.',422)
    payload={'to':destination.lstrip('+')}
    if template:
        payload.update(template=template,template_language=config.whatsapp_template_language,template_variables=variables or [])
    else:
        payload['text']=text
    try:
        with httpx.Client(timeout=8,follow_redirects=False) as client:
            response=client.post(f'https://api.whatsmcp.com/v1/accounts/{config.whatsmcp_account_id}/messages',headers={'X-API-Key':config.whatsmcp_api_key},json=payload)
    except httpx.HTTPError:
        # A timeout may happen after acceptance. Never retry a secret message automatically.
        raise WhatsMCPError('WhatsApp delivery could not be confirmed. Check your phone before requesting another code.') from None
    if response.status_code==429:
        raise WhatsMCPError('WhatsMCP message quota or rate limit reached. Wait before requesting another message.',429)
    if response.status_code==409:
        raise WhatsMCPError('The WhatsMCP sender is disconnected. Reconnect it in the WhatsMCP console.')
    if response.status_code in {401,403}:
        raise WhatsMCPError('WhatsMCP rejected the server credentials or this account plan. Check the console configuration.')
    try:
        status=response.json().get('status')
    except (ValueError,AttributeError):
        status=None
    if response.status_code not in {200,202} or status not in {'sent','queued'}:
        raise WhatsMCPError('WhatsMCP did not accept this message. Check the sender account and template configuration.')
    return {'provider_status':status,'delivery':'whatsmcp','external_sent':True}


class WhatsMCPOtpProvider:
    def send(self,destination,code,contact_id):
        return send_message(destination,f'Your Helm verification code is {code}. It expires in 10 minutes. Do not share it.',settings().whatsapp_auth_template,[code])


class WhatsMCPNotification:
    def send(self,contact,url):
        config=settings()
        origin=urlparse(config.public_quote_origin)
        if origin.scheme!='https' or not origin.hostname or origin.username or origin.password or origin.path not in {'','/'} or origin.query or origin.fragment or origin.hostname in {'localhost','127.0.0.1','::1'}:
            raise WhatsMCPError('Set PUBLIC_QUOTE_ORIGIN to the HTTPS address that opens this prototype on your phone.')
        if url=='/broker.html':
            path=url
        elif re.fullmatch(r'/(?:my-quotes|quote-dashboard)#[A-Za-z0-9_-]{43}',url):
            path=url
        elif url in {'/my-quotes','/quote-dashboard'}:
            path='/my-quotes'
        else:
            raise WhatsMCPError('A valid private quotation link is required.')
        absolute=config.public_quote_origin.rstrip('/')+path
        return send_message(contact.data['destination'],'Your private Helm quotation dashboard: '+absolute+' Keep this link private. All insurance quotations are fictional.',config.whatsapp_utility_template,[absolute])
