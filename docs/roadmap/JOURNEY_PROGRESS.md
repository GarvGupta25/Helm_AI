# Helm AI journey implementation progress

The owner authorized continuing all phases without repeated approval pauses. In-product human approval of outgoing drafts remains required. Everything here is synthetic; the live release guard remains enabled.

## Phases 1–4

Commits 05db3a1 through fc622f1 implement the shared canonical manual/guided intake, confirmation and undo, deterministic family recommendations, comparison/shortlist/what-if, grounded policy Q&A and its 50-question corpus, simulated contact verification, exact-recipient consent, private idempotent quote requests, and delayed fictional insurer responses. Focused checks are included with each checkpoint.

## Phase 5 — private quotation delivery

Checkpoints: 4f36fa3 (expiring hashed access/exchange), b574a4c (dashboard/PDF/frozen Q&A), and the notification checkpoint containing this report.

- Case links last 24 or 48 hours, exchange once into a private HttpOnly dashboard cookie, and support logout/revocation/recovery. Link secrets are delivered only in the encrypted private demo inbox.
- A separate seven-day protected demo mailbox permits re-verification when the 24-hour intake expires. This simulates contact verification and does not prove real account ownership.
- Received/expired quotations have comparison, authorized PDFs, and answers from frozen plan facts. Notifications use persisted jobs, explicit channel opt-in, quiet hours/time zones, expiry reminders, deduplication, and opt-out. No external provider is called. Demo templates are not provider-approved WhatsApp templates.
- Fresh focused results: dashboard API/PDF test 1 passed; access/contact/notifications tests 6 passed; intake browser tests 3 passed, including RTL/scoped axe, draft persistence, request, private exchange, quotation download, and dashboard scoped axe. Frontend typecheck, scoped lint, and demo build passed. A proxy-origin mismatch found by the browser test was fixed against explicitly configured trusted development origins; unrelated origins remain rejected.
- Local API and worker use only .runtime/uk-e2e.db. Migration 0005 was applied to that existing scratch database. No production database, physical device, live insurer, email or WhatsApp service was exercised. PostgreSQL concurrency remains a launch prerequisite.

## Phase 6 — in progress

Assigned broker cases, separate entry point, versioned review and simulated sign-off are the remaining checkpoints. Actual final checks and limitations will be recorded here when complete.
