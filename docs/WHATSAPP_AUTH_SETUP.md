# WhatsApp OTP and private-link authentication

Implemented 25 October 2026. All insurance products remain synthetic. Twilio delivery has **not** been tested with an actual account or phone. No credentials were created, read from the Console, or committed. Trial entitlement and template approval must be checked by the account owner.

## Current prototype: demo login, Twilio parked

The owner requested demo WhatsApp authentication until upgrading Twilio. `npm run api:prototype` now selects explicit guarded mock mode regardless of saved provider settings. `npm run worker:prototype` keeps notifications local. Twilio's implementation, SDK, validation, webhooks and tests are preserved; activation settings are commented out in `.env.example`. They do not run in demo mode. This is a development-only flow and does not prove phone ownership or grant customer/broker roles.

Use **Generate demo OTP**, enter the displayed six-digit code (or **Use demo OTP**), then **Show demo sign-in link** and **Continue to my quotes**. The original reviewed selection, case creation, synthetic quotation worker, link interstitial, single-use exchange and dashboard remain. No provider credentials, allowlist or public tunnel are required for this local flow. The OTP expires in five minutes with five attempts; the access link expires in ten minutes. Resend throttling and number-format validation remain.

## Architecture and scope

Helm uses React/TypeScript/Vite with React Router, FastAPI/Pydantic, SQLAlchemy/Alembic and encrypted journey state. Existing customer and professional authentication uses Supabase; these roles are not granted by WhatsApp verification. The quotation journey already has its own reviewed selection, verified Contact, Case, hashed Grant and HttpOnly dashboard session. This integration extends that existing flow; it does not introduce a parallel user database or link a phone to an unrelated Supabase account.

Inspected `config.py`, `main.py`, journey `verification.py`, `contact.py`, `access.py`, `wizard_access.py`, `case_models.py`, `delivery.py`, `notifications.py`, `retention.py`, `router.py`, frontend `Verification.tsx`, `AccessChoice.tsx`, `Dashboard.tsx`, the wizard contract and existing verification/access tests. The implementation adds small Twilio and verified-link modules and the official Python SDK. No database schema changes or live migration are needed; migration head remains 0008.

`/get-cover/verify` → server-normalized number and explicit code/link consent → `/verify/start` → six-digit code → `/verify/check` → verified contact → automatic ten-minute link to the same number → `/get-cover/access` delivery status → `/my-quotes#TOKEN` → deliberate POST `/access-links/exchange` → existing private quotation dashboard. URL fragments keep tokens out of HTTP access logs. The landing page removes the fragment from history and requires a button press, so link previews cannot consume it. All listed API suffixes use `/api/journey`.

The UK audience's +44 default stays; +91 and other country codes are selectable. An international number is normalized and validated using phonenumbers server-side. Form validation, six-digit paste, keyboard focus, resend cooldown, change-number and clear error states remain in the current UI. WhatsApp consent does not grant marketing or quotation-update consent.

## Choose a mode

| Purpose | Configuration | Behaviour |
|---|---|---|
| Existing installation | Keep current OTP_DELIVERY_MODE | Existing WhatsMCP, Cloud API, email and legacy console flows remain |
| Isolated development | `OTP_DELIVERY_MODE=mock`, `WHATSAPP_MOCK_AUTH=true`, `APP_ENV=development` | Private developer OTP and link controls; explicitly simulated ownership |
| Managed Twilio after entitlement is confirmed | `OTP_DELIVERY_MODE=twilio`, `TWILIO_OTP_PROVIDER=twilio_verify` | Twilio controls OTP lifecycle; current new trials require an upgrade to create your own Verify service |
| Trial custom-code fallback | `OTP_DELIVERY_MODE=twilio`, `TWILIO_OTP_PROVIDER=custom` | Six random digits, HMAC digest bound to contact, five-minute expiry; predefined verification template |
| Production transport | Twilio mode, registered sender, `TWILIO_SANDBOX=false`, approved ContentSid | Approved template delivery; broader application production guard still stays closed |

No silent fallback occurs when Verify is unavailable: change configuration explicitly, restart and request a new code. In-flight attempts cannot switch OTP provider. Verify attempts have a local ten-minute ceiling and five failed-check ceiling; Twilio's managed expiry/attempt rules can reject earlier. Custom mode uses five minutes and five failed checks. Resend uses the same endpoint controls: 60 seconds, three sends/hour per number and journey session, plus existing per-IP limiter. Twilio errors are sanitized, and ambiguous network failures never trigger an automatic secret resend.

## Twilio Console actions (owner required)

1. Create an account at [Try Twilio](https://www.twilio.com/try-twilio), verify developer identity/contact and inspect the account's trial eligibility, country restrictions, expiry and remaining free units. Do not assume unlimited free messaging or entitlement to a specific channel.
2. In Console Home, open **Try it out → Communications → Send a WhatsApp message**. Some accounts show legacy **Messaging → Try it out → Send a WhatsApp message**. Accept Sandbox terms when prompted. Read the actual sender and join instructions shown for your account.
3. From the tester's WhatsApp, scan the QR code or send `join <your code>` to that sender. Wait for the Sandbox enrollment confirmation. Add/verify the tester under the trial's verified-recipient flow too; these are separate requirements. Current trial documentation allows up to five verified numbers shared across products, but inspect your Console's actual limit.
4. In the trial page, send a predefined message and inspect its API example and Logs. Copy the actual `whatsapp:+...` sender; do not assume every trial uses the legacy shared number.
5. Obtain Account SID and Auth Token from **Account Info / API keys & tokens**. Store only in ignored `backend/.env` or your server secret manager. Never paste them into frontend settings, screenshots or Git.
6. Open **Verify → Services**, create/select a service and obtain its `VA...` SID. Check WhatsApp availability in that service/account. Configure six-digit codes. Test the WhatsApp channel against a verified recipient. This integration sends `channel=whatsapp` and verifies the returned verification SID; it never treats a locally generated code as valid for a managed attempt.
7. If Verify WhatsApp is unavailable, select custom mode and find the **Verification Codes** predefined Sandbox template shown in your Console. Copy its actual `HX...` ContentSid into `TWILIO_OTP_CONTENT_SID`. The current legacy template has variables `1=Helm AI`, `2=code`. Compare your Console's template contract before enabling; never use an invented SID or a production authentication template with a different variable contract.
8. Expose the local website and API through a trusted HTTPS development tunnel/proxy. A phone cannot open the computer's `localhost`. The public site must forward `/api` to the same API. Set PUBLIC_QUOTE_ORIGIN to the public website origin and TWILIO_WEBHOOK_ORIGIN to the exact externally reachable callback origin, with no path or trailing query.
9. Set Sandbox **When a message comes in** to `https://YOUR_CALLBACK_ORIGIN/api/journey/webhooks/twilio/inbound`, POST. Status callback URL is attached by code: `/api/journey/webhooks/twilio/status`. Your proxy must preserve those paths. Signatures are validated against configured HTTPS URLs, not untrusted forwarded headers. Verify product delivery is tracked by the Verify service/Console; Messages callbacks track custom OTP and magic-link sends.
10. Select the correct magic-link strategy below. Complete a quote selection, request OTP, receive it, submit it and inspect delivery status. If delivery is accepted, confirm actual receipt on the phone and delivery callback. These are manual checks; automated fixtures do not prove real delivery.

Code automates generation, hashing, verification, expiry, rate controls, link issuance and redemption, callback validation and delivery-state updates. Account creation, joining, recipient eligibility, entitlement and template/sender approval cannot be automated by this repository.

## Trial restrictions and magic links

**Newer template-only trial:** Twilio's current trial documentation permits only the supplied template messages, with restricted editable parameters. Leave `TWILIO_LEGACY_SESSION_MESSAGES=false`. OTP may be permitted; a custom magic-link message may be blocked. The app reports **blocked**, creates no authenticated dashboard session and does not return a usable Twilio link to the browser. Continue full local testing in mock mode. Do not hide a URL in an unrelated predefined template.

**Legacy Sandbox session mode:** Only if your account explicitly supports permitted free-form session replies, set `TWILIO_LEGACY_SESSION_MESSAGES=true`. Have the enrolled tester send an inbound WhatsApp message. The signature-checked webhook fetches that message from Twilio, checks sender/destination/direction and timestamps the 24-hour window from the message creation time, so replaying the webhook cannot extend it. A valid active window is required before a Body message containing a link is submitted. The flag cannot bypass provider/account restrictions. API rejection is shown as failure. Sandbox enrollment expiry (currently three days in legacy docs) differs from the 24-hour free-form window. Rejoin when necessary. Shared Sandbox throughput is limited; this is not a load-testing transport.

**Production template mode:** `TWILIO_SANDBOX=false`, registered sender and approved `TWILIO_MAGIC_LINK_CONTENT_SID`. The implementation passes ContentVariables `{"1":"FULL_HTTPS_PRIVATE_URL"}`. Provision a compliant template with this exact contract and obtain provider approval. Some authentication categories do not permit arbitrary URL sign-in messages; have Twilio/Meta confirm an eligible category and URL/fragment support for your actual template. A ContentSid alone is not proof of approval.

Provider acceptance is never proof of delivery. The UI distinguishes pending, accepted/queued, sent, delivered/read, failed/undelivered, blocked and mock. Signed duplicate callbacks are idempotent and earlier states cannot overwrite later states. No phone, code, message body or full token URL is logged by these modules. Message SID/error code are stored in encrypted state. Callback records are associated by exact MessageSid; existing seven-day contact/job cleanup and expired-window cleanup apply.

Primary references checked 25 October 2026: [trial WhatsApp](https://www.twilio.com/docs/usage/trials/try-out-whatsapp), [legacy Sandbox](https://www.twilio.com/docs/whatsapp/sandbox), [Verify quickstarts](https://www.twilio.com/docs/verify/quickstarts), [request validation](https://www.twilio.com/docs/usage/security), [authentication content](https://www.twilio.com/docs/content/whatsappauthentication). Follow your account's applicable flow when those trial experiences differ.

## Environment reference

Use `backend/.env.example`; real `.env` is ignored. Never use VITE-prefixed private settings.

| Variable | Source / meaning |
|---|---|
| OTP_DELIVERY_MODE | `twilio` or explicitly isolated `mock`; existing transports unchanged |
| TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN | Console Account Info / API keys & tokens |
| TWILIO_VERIFY_SERVICE_SID | Verify Services, required for managed mode |
| TWILIO_WHATSAPP_FROM | Exact Console WhatsApp sender, including `whatsapp:` |
| TWILIO_OTP_PROVIDER | `twilio_verify` (default) or `custom` |
| TWILIO_OTP_CONTENT_SID | Supplied verification-code HX template, custom mode only |
| TWILIO_MAGIC_LINK_CONTENT_SID | Approved registered-sender template, variable 1 is full URL |
| TWILIO_SANDBOX | true for trial/Sandbox, false for registered production sender |
| TWILIO_LEGACY_SESSION_MESSAGES | false by default; legacy account permission plus signed window required |
| PUBLIC_QUOTE_ORIGIN | HTTPS website origin reachable on the tester's phone |
| TWILIO_WEBHOOK_ORIGIN | HTTPS origin used by Twilio for both exact callback paths |
| OTP_ALLOWLIST | JSON array of exact normalized tester numbers, e.g. `["+919876543210"]`; use your enrolled number |
| MAGIC_LINK_EXPIRY_MINUTES | 1–10, default 10; shorter than legacy 24/48-hour links |
| RESEARCH_STATE_KEY | Stable existing Fernet key; isolated prototype launcher provides its own ignored local key |
| WHATSAPP_MOCK_AUTH | Explicit true required alongside mock delivery and development/test APP_ENV |

Twilio mode fails startup on incomplete/unsafe configuration. Mock mode fails outside explicit development/test. No mock fallback is enabled by missing real credentials. The default transport is not changed automatically. No new production authentication rollout or live database migration is authorized by installing this feature.

## Local development

Install `uv`, then `uv sync --project backend`; `npm ci` and `npm --prefix frontend ci`. Use Python 3.12/3.13 as required by the project. Keep real credentials in ignored backend/.env.

For isolated mock testing set the following in backend/.env:

```dotenv
APP_ENV=development
OTP_DELIVERY_MODE=mock
WHATSAPP_MOCK_AUTH=true
```

Start **normal** `npm run api:prototype`, then `npm run worker:prototype`; start frontend with `VITE_QUOTE_WIZARD=true` (PowerShell: `$env:VITE_QUOTE_WIZARD='true'; npm --prefix frontend run dev -- --port 4174`). These prototype launchers select ignored `.runtime` databases and a stable local key. Use the printed local URL. The separately named `uk_test_server.py` deliberately forces old console mode and must not be used to exercise the mock UI or real messaging. Stop normal API before automated browser suites; inspect exact PIDs first.

Complete the guided quote intake and selection, then open `/get-cover/verify`. Select a country, enter a valid-format test number, consent and choose **Generate demo OTP**. Enter the displayed OTP or choose **Use demo OTP**, then submit it. On success choose **Show demo sign-in link**, then **Continue to my quotes**. Deliberately continue on the landing screen. You should reach the existing private quotation dashboard. No real account ownership or message delivery is proved.

For Twilio after upgrade/approval, uncomment and fill the private Twilio settings, replace mode with twilio, disable mock, configure credentials/allowlist/origins and select the appropriate strategy above. Start the API with `uv run --project backend python backend/scripts/prototype_server.py --allow-configured-sandbox` and the worker with `uv run --project backend python backend/scripts/journey_worker.py --allow-configured-sandbox`; the ordinary npm prototype commands deliberately stay local. Restart after settings changes. Use your actual enrolled number for real delivery. Codes and URLs are never exposed by developer endpoints in Twilio mode. Ambiguous failure requires Console inspection and reverification rather than blind resend of the same secret. Resend-code is throttled; requesting a new code replaces the active local attempt. An expired/used link requires reverification.

## Security and testing checklist

- Number substitution is prevented: all link destinations come from the server's current verified Contact, bound to the reviewed selection. The send-link endpoint accepts no destination and requires server verification within ten minutes.
- Custom codes have a cryptographic HMAC, five attempts and expiry. Managed checks use Twilio's verification SID; never custom validation. Failed provider checks count against the local limit.
- Twilio tokens use 32 random bytes, SHA-256 grant lookup, short expiry and an atomic conditional claim in the same transaction as session creation. Only the hash persists for Twilio links; no plaintext or encrypted reusable link is kept in jobs. This means an interrupted send cannot recover the same raw token; reverify instead. Explicit mock uses the existing encrypted private developer inbox.
- Redemption rotates to a separate random HttpOnly, SameSite=Strict cookie, Secure on HTTPS, bounded to the link's remaining lifetime and maximum two hours. Existing same-origin checks, case consent/expiry checks, no-referrer and no-store responses remain. Supabase roles and broker assignment checks stay separate.
- Check invalid number; wrong/expired/consumed OTP; five wrong attempts; 60-second resend; three sends/hour; request before verification; wrong session; provider switch mid-attempt; provider timeout; blocked trial; active signed inbound window; forged callbacks; duplicate/out-of-order status; number-bound template; successful redemption; expired/replayed token; simultaneous redemption; missing credentials and production mock rejection.
- In mock mode verify desktop/mobile keyboard operation, paste all six digits, change number, loading/error text, refresh delivery status, single-use landing and signed-out dashboard recovery.
- External checks still required: actual trial entitlement, template variable contract/approval, live message receipt, publicly reachable callback signatures, physical phones, PostgreSQL load/concurrency, distributed rate limiting and operational monitoring. No claim of production clearance is made.

## Troubleshooting

Unavailable send button/startup: check selected mode, required SID formats, sender, HTTPS origins, allowlist and stable storage key. Invalid-number rejection: choose correct calling code or use complete E.164. 429: respect cooldown, hourly limits and provider throughput; do not disable limiters. 63015: check Sandbox enrollment. Trial verified-recipient rejection: verify that tester in the Console too. 401/403/provider failure: inspect server credential permissions in Console without copying secrets to logs. Template error: verify the actual HX template, approval, language and variable contract; a production template cannot be substituted for the two-variable Sandbox verification template. Signature 403: compare exact external URL, account and Auth Token; do not disable validation. Accepted but not received: inspect Message SID delivery logs/callback, phone eligibility and session restrictions. An already-used or expired link requires verification again.

## Production transition

Upgrade the account; complete Twilio/Meta business compliance, register and verify the real sender/display name; obtain approved OTP and eligible magic-link templates and confirm their variable contracts; use production secrets, HTTPS website/callback origins and appropriate exact recipient policy; disable Sandbox/session-body mode and mock; set ContentSid; test provider receipt and signed callback delivery. Rehearse migrations against an explicitly chosen backed-up database if other releases require them. Add operational alerting and privacy retention review; validate multi-instance abuse controls, proxy/cookie behaviour and PostgreSQL concurrency. Keep the existing whole-application production guard closed until the wider repository's launch review is complete. Provider registration/configuration changes do not require rebuilding the frontend flow.
