# Twilio authentication verification — 25 October 2026

## Demo default follow-up — 25 October 2026

At the owner's request, normal prototype startup now explicitly enables guarded mock WhatsApp authentication. The worker's normal command leaves notifications local. Twilio activation settings are commented out; its provider, SDK, webhooks, verification controls and tests remain for later upgrade/approval. Re-enabling requires private env configuration and the explicit real-delivery launcher flag documented in WHATSAPP_AUTH_SETUP.md. No database migration was added.

The form accepts a valid-format phone number, displays its generated demo OTP, supports manual entry or **Use demo OTP**, and opens the existing private-link confirmation and quotation dashboard. Demo copy does not claim phone ownership or external delivery. Docked broker help keeps the code boxes accessible on mobile. Expiry, attempts, cooldown, one active code, selection binding, single-use links and dashboard session limits remain.

Checks: focused backend suite `test_prototype_mode.py`, `test_twilio_auth.py`, `test_wizard_verification.py`: **14 passed**; scoped Ruff passed; frontend check, lint and demo build passed; Vitest **16 passed**. `tests/wizard/twilio.spec.ts`: **3 passed**, including demo phone entry and real-provider controls hidden at desktop/mobile widths. Additional Playwright smoke against the actual running mock API and built preview at 1440px and 375px: **2 passed**, through OTP, private-link exchange, dashboard and received synthetic quotations/PDF link. Axe found no serious/critical wizard violations. Local screenshot evidence and the temporary smoke harness are ignored under `.runtime`.

The first mobile smoke reused the desktop number within its 60-second resend cooldown and was correctly rejected. Changed the fixture to use a separate valid-format test number; both viewports then passed together. No limiter was weakened. Final preview config reports mode=mock, mock=true, real_delivery=false. Real WhatsApp delivery, paid account approval, physical devices, manual screen readers and PostgreSQL concurrency were not tested. The prototype remains local and is not a production authentication rollout.

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
