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

## Phase 6 — delivered synthetic workflow

Checkpoints 9b67549, 750e1b0 and 4b78b43 implement consented/assigned cases, a separate authenticated broker entry, and human document review. The final lifecycle checkpoint adds retention cleanup, recovery/preview hardening, private broker notices, an operator assignment command, meaningful negative and two-visitor/two-broker integration coverage, scoped UI label fixes and updated setup/handover documentation.

- Broker access is enforced on queue/counts/inbox/detail/notes/messages/documents/approval/dispatch: valid server-verified broker identity, exact case assignment, active sharing consent and unexpired case. Cases without assignment stay private.
- Early help works with an incomplete profile after explicit contact/sharing review. Automatic cases use the reviewed selection/request boundary. Both are idempotent within their defined triggers; matching fictional emails never merge visitors.
- The separate Vite multipage portal has state/urgency/reference filters, pagination, confirmed facts, selected plans, contact/channel/consent summaries, notes, customer thread, documents, checklist and audit views. Existing archived professional bundles were not restored wholesale.
- AI-assisted demo documents use controlled templates, source references and internal draft labels. Edit creates a revision, revokes prior approval and returns the case to progress. Approval binds content fingerprint, recipient/purpose scope, profile version and authenticated assigned broker. Dispatch rechecks all authority, current profile and live quotation snapshots; it writes only a simulated delivery/thread. A plain state transition cannot submit a case.
- Intake expiry clears encrypted drafts/history/runs at 24 hours; separately consented cases last seven days. Health withdrawal removes derived case/document/job/grant copies. Tests cover fresh/upgrade migrations, independent retention, expiry/recovery, prompt-instruction rejection paths and capability boundaries. The live source guard now includes journey and broker sources as well.

## Final verification — 24 October 2026

| Check | Actual result |
| --- | --- |
| `DATABASE_URL=sqlite://`, `GROQ_API_KEY=''`, `uv run --project backend pytest backend/tests -q` | **482 passed, 1 skipped**, 1 dependency deprecation warning, 80.78 seconds |
| Skipped backend check | Existing PostgreSQL-only intake-agent database-role permission test. No PostgreSQL role or concurrency claim is made. |
| `uv run --project backend ruff check backend/app backend/tests backend/scripts` | Passed |
| `npm --prefix frontend run lint:uk` | Passed, including journey and broker source |
| `npm --prefix frontend test` | **10 passed**, 2 files |
| Frontend TypeScript check and demo build with `VITE_NEXT_CHAT_UI=true` | Passed; both index.html and broker.html emitted. Existing Home.tsx static/dynamic import warning remains non-blocking. |
| `npx playwright test -c playwright.uk.config.ts --output .runtime/journey-final-browser-results` | **23 passed**, including scroll geometry/composer regressions, canonical customer request → private exchange → PDF, RTL/scoped axe, legacy research flow, broker auth-unconfigured desktop/mobile, and broker document editing/checklist/approval UI fixture |
| `npx playwright test -c playwright.config.ts` | **9 passed** — preserved customer marketplace, claim-message and portal-role guidance paths |
| Production build | **Expected failure, exit 1**: live-market/regulatory/product/historical-migration blockers remain. The guard was not bypassed. |
| Archive snapshot integrity | All **70 recorded archived Git blobs** still match the safety-tag ledger; no archive paths changed since journey baseline 44213bd. Working-tree byte hashes differ because of checkout line endings; no exact-byte match claim is made. |
| Original `archive/verify_preservation.py` | Still fails its old site-split-only baseline policy: edited `.github/workflows/checks.yml` lacks an original snapshot. The script also forbids later backend/package/docs evolution. This is not a passing full preservation verifier; direct archived-blob integrity and customer regressions were checked separately. |
| Local prototype | API/worker use ignored scratch SQLite/key; preview serves the built site at 127.0.0.1:4174. No live contacts/providers/production database were exercised. |

The backend suite includes complete two-customer/two-broker isolation and sign-off, same-email non-merging, revoked sharing after approval, stale document/profile rejection, immutable adapter-price validation, timeout exhaustion/partial results, private PDFs, hashed-link purpose/replay/expiry and retention/migration checks. The policy corpus contains 50 versioned question cases evaluated against three fictional plans, including unknown/refusal cases.

The broker browser workflow deliberately uses mocked auth/API fixtures to test the UI. API role/assignment/consent/approval behavior is tested against FastAPI independently. There was no configured real Supabase broker sign-in in this session. Physical devices, screen readers, real transports and PostgreSQL concurrency remain outside the measured results.

Generated browser artifacts are retained locally under ignored `.runtime`; source-controlled legacy screenshots/reports are restored after verification to avoid committing unrelated generated binary changes. Preview screenshots from direct browser inspection are `.runtime/journey-intake-preview.png` and `.runtime/journey-broker-entry.png`; they contain no raw capabilities or OTPs.

## Implemented simplifications and remaining launch work

- The session is the guest identity. Bounded encrypted aggregates hold consent/audit/note/message/question records. Eleven additive journey tables provide the needed boundaries without the sixteen-table Phase 0 sketch.
- Manual and guided intake use a controlled deterministic extractor; policy answers are reviewed source-backed templates; documents are controlled internal draft templates. No external journey LLM provider is called. Provider integration is deferred, with the existing consent/human-approval rules still required.
- The broker is a separate entry in the existing Vite package; it reuses auth and dependencies. The older professional portals stay archived.
- Fake email/WhatsApp delivery means the protected inbox, not real contact ownership or external sending. Templates are labeled demo-only, not provider-approved. Seven-day mailbox recovery is within the same protected demo browser context.
- PostgreSQL race/locking/multi-worker tests, operational monitoring/supervision/backups, real Supabase broker configuration, real-provider/device/screen-reader checks, approved products and regulatory/privacy/security sign-off remain launch work. The live release guard remains intentionally closed.

## Actual development ledger

Phase 0 was `44213bd`. The following are **18 substantive implementation commits** after that baseline, authored Utkarsh Raj. The final row names its own containing checkpoint to avoid a self-referential hash.

| No. | Commit | Checkpoint |
| --- | --- | --- |
| 1 | [05db3a1](https://github.com/GarvGupta25/Helm_AI/commit/05db3a1) | feat(intake): add canonical draft schema and isolated version storage |
| 2 | [58dcb25](https://github.com/GarvGupta25/Helm_AI/commit/58dcb25) | feat(intake): confirm shared drafts with consent versioning and extraction fallback |
| 3 | [04feb8f](https://github.com/GarvGupta25/Helm_AI/commit/04feb8f) | feat(intake): add lossless manual and guided interview modes |
| 4 | [b69fe66](https://github.com/GarvGupta25/Helm_AI/commit/b69fe66) | fix(intake): preserve essential needs and complete accessible RTL recovery |
| 5 | [ef1d6a7](https://github.com/GarvGupta25/Helm_AI/commit/ef1d6a7) | feat(recommendations): apply canonical constraints and deterministic family pricing |
| 6 | [0a0255c](https://github.com/GarvGupta25/Helm_AI/commit/0a0255c) | feat(comparison): persist version-bound shortlists and explainable what-if views |
| 7 | [3124e09](https://github.com/GarvGupta25/Helm_AI/commit/3124e09) | feat(policy-qa): return grounded plan facts and deterministic scenario answers |
| 8 | [ea852db](https://github.com/GarvGupta25/Helm_AI/commit/ea852db) | feat(policy-qa): add bounded conversations and fifty-question citation evaluation |
| 9 | [6c02717](https://github.com/GarvGupta25/Helm_AI/commit/6c02717) | feat(contact): verify simulated contacts and record purpose-specific sharing consent |
| 10 | [d41a4ab](https://github.com/GarvGupta25/Helm_AI/commit/d41a4ab) | feat(quote-requests): create private consented cases and idempotent insurer requests |
| 11 | [fc622f1](https://github.com/GarvGupta25/Helm_AI/commit/fc622f1) | feat(insurer-demo): process delayed quotations with retries and consented request review |
| 12 | [4f36fa3](https://github.com/GarvGupta25/Helm_AI/commit/4f36fa3) | feat(dashboard-access): exchange hashed expiring case links with replay protection |
| 13 | [b574a4c](https://github.com/GarvGupta25/Helm_AI/commit/b574a4c) | feat(quote-dashboard): compare and download authorized synthetic quotations |
| 14 | [60559df](https://github.com/GarvGupta25/Helm_AI/commit/60559df) | feat(notifications): deliver demo updates and deduplicated quiet-hour reminders |
| 15 | [9b67549](https://github.com/GarvGupta25/Helm_AI/commit/9b67549) | feat(broker-cases): enforce consented handoff assignment and audited transitions |
| 16 | [750e1b0](https://github.com/GarvGupta25/Helm_AI/commit/750e1b0) | feat(broker-workspace): add a separate authenticated multi-client case queue |
| 17 | [4b78b43](https://github.com/GarvGupta25/Helm_AI/commit/4b78b43) | feat(broker-review): approve exact draft revisions before simulated dispatch |
| 18 | This checkpoint | test(journey): verify the complete synthetic customer-to-broker lifecycle |

The owner authorized direct pushes to the shared repository. Development checkpoints were fetched/integrated and pushed in batches; the final handover verifies local HEAD against origin/main. No force push, archive rewrite, live release or credential commit was performed.
