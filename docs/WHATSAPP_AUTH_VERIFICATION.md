# Twilio authentication verification — 25 October 2026

## Completed local checks

| Check | Actual result |
|---|---|
| Full backend suite, `DATABASE_URL=sqlite://`, empty GROQ_API_KEY, `PYTHONPATH=backend`, root `.venv/Scripts/python.exe -m pytest backend/tests -q` | **521 passed, 1 skipped** in 131.99 s at the integration baseline |
| Final focused suite: `test_twilio_auth.py`, `test_wizard_verification.py`, `test_wizard_access.py`, `test_journey_access.py` | **15 passed** in 50.69 s after final managed-check transaction and cookie lifetime changes; includes three additional expiry/race cases added after the full run |
| Ruff: `python -m ruff check backend/app backend/tests/test_twilio_auth.py` | Passed |
| Frontend `npm --prefix frontend run check`, `lint:uk` | Passed |
| Frontend `npm --prefix frontend test` | **16 passed**, six test files |
| `VITE_QUOTE_WIZARD=true npm --prefix frontend run build` | Demo build passed; existing Home.tsx mixed static/dynamic-import warning; production guard remains intact |
| Playwright wizard verification + Twilio specs | All **7 distinct cases passed**: six in the main batch, mock case on its corrected targeted rerun |
| Mobile and desktop visual/accessibility checks | 375/1440 px captures inspected; no serious/critical axe violations on Twilio blocked status; existing verification screens also pass axe |
| `uv lock --project backend --check` | Passed; official Twilio SDK and its dependencies locked |

The full backend run preceded the last three expiry/race tests and final small transaction/cookie edits. The final focused run verifies those changes; do not describe this as a 524-test full-suite run.

The Windows checkout initially lacked the newly pulled phonenumbers dependency and uv; installed local tools/dependencies to run checks. No credentials or configured customer database were used. Automated browser checks used `uk_test_server.py`, isolated `.runtime/uk-e2e.db`, console delivery and no live Groq. Twilio UI tests intercept provider-facing API responses; backend tests use a fake Twilio client and real request-signature implementation. These checks prove local behaviour, not real provider entitlement or WhatsApp receipt.

## Meaningful security coverage

- Managed Verify success/failure, SID-bound number checks, no custom-code fallback or hash acceptance for a managed attempt.
- Six-digit custom OTP template variables, hashed/encrypted contact state, five wrong attempts, expiry, replacement/resend cooldown and hourly caps.
- Unverified/mismatched-session link requests rejected; Twilio token and OTP developer endpoints unavailable; phone from trusted server state only.
- Trial restrictions block free-form links by default without reporting delivery. Explicit legacy Sandbox mode requires signed inbound evidence. Registered-sender template path tested separately.
- Missing credentials and unsafe production/mock settings fail; provider error bodies sanitized.
- Official SDK signatures checked for inbound/status callbacks; forged signatures rejected; duplicate/out-of-order callbacks handled.
- Ten-minute grant lifetime, no recoverable Twilio link in stored job data or public response, deliberate POST exchange, no CSRF cross-origin exchange, new HttpOnly/SameSite cookie and replay rejection.
- Two concurrent redemptions against a file-backed SQLite database produce exactly one success and one 410 response, with exactly one dashboard session.
- Mock full HTTP flow reaches existing dashboard with simulated ownership explicitly false; private mock link requires verified session and is unavailable after consumption or outside development/test.

## Failures found and corrected during development

The first expiry test iteration omitted its timedelta import; fixed the test and reran the focused suite successfully. The initial browser token-link selector included the accessibility skip link; restricted it to the wizard. The mock browser fixture initially omitted necessary-cookie setup, then asserted a status before navigation completed; corrected fixture consent and waited for the destination heading. Six main-batch browser cases and the final targeted mock case pass. No limiter was relaxed, no genuine application check was removed, and no public developer bypass was added.

## Remaining external verification

No real Twilio credentials, account entitlement, sender approval, template approval, OTP receipt or WhatsApp magic-link receipt was tested. The owner must follow [the setup guide](WHATSAPP_AUTH_SETUP.md), check whether the account is the newer template-only trial or legacy Sandbox, enroll and verify a recipient, configure public HTTPS origins and signed callbacks, and verify actual delivered/read status on a phone. Physical-device testing, manual screen readers and PostgreSQL/multi-instance concurrency and abuse controls remain external checks. No live migrations, deployment or production clearance occurred.

## Main changed files

- `backend/app/journey/twilio_auth.py`: official SDK provider, managed OTP checks, trial policy gates, signature validation and delivery callbacks.
- `backend/app/journey/whatsapp_link.py`: verified contact proof, existing case/grant composition, safe delivery status and explicitly private mock inbox.
- `backend/app/journey/verification.py`: opt-in provider dispatch, per-attempt provider identity, resend and automatic link issuance.
- `backend/app/journey/access.py`: short auth-link lifetime, digest-only Twilio token persistence, atomic redemption, bounded session cookie and provider-aware recovery.
- `backend/app/journey/wizard_access.py`, `contact.py`: preserve legacy APIs while suppressing Twilio/mock link disclosure from general responses/inbox.
- `backend/app/config.py`, `main.py`, `.env.example`, `pyproject.toml`, `uv.lock`: private configuration, safe startup, routes and locked official SDK dependency.
- `frontend/src/journey/wizard/Verification.tsx`, `AccessChoice.tsx`, `WhatsAppLink.tsx`: existing-style OTP input/resend, explicit simulation and truthful delivery screen.
- `backend/tests/test_twilio_auth.py`, `tests/wizard/twilio.spec.ts`, updated verification browser spec: provider/security/concurrency and desktop/mobile UI checks.
- Setup/verification docs, README, AGENTS, PROJECT_OVERVIEW and quote workflow: configuration, current behaviour and operational limits.
