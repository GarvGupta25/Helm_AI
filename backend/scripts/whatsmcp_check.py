"""Read-only sender check. Never prints keys, phone numbers, codes or account IDs."""
import httpx

from app.config import settings
from app.journey.whatsmcp import configured


def main():
    config=settings()
    if not configured():
        print('Setup incomplete: fill WHATSMCP_API_KEY and WHATSMCP_ACCOUNT_ID in backend/.env.')
        return 1
    try:
        with httpx.Client(timeout=10,follow_redirects=False) as client:
            response=client.get('https://api.whatsmcp.com/v1/accounts',headers={'X-API-Key':config.whatsmcp_api_key})
        if response.status_code!=200:
            print(f'WhatsMCP refused the account check (HTTP {response.status_code}). Check credentials and plan.')
            return 1
        account=next((a for a in response.json().get('accounts',[]) if a.get('account_id')==config.whatsmcp_account_id),None)
        ready=bool(account and account.get('status')=='live')
        print('Configured sender connected.' if ready else 'Configured sender is unavailable. Link or reconnect it in the WhatsMCP console.')
        return 0 if ready else 1
    except (httpx.HTTPError,ValueError,TypeError,AttributeError):
        print('Account check could not complete. No message was sent.')
        return 1


if __name__=='__main__':
    raise SystemExit(main())
