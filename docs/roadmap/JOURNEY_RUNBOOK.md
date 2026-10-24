# Helm AI journey demo — developer and operator runbook

Updated 24 October 2026. Repository: [GarvGupta25/Helm_AI](https://github.com/GarvGupta25/Helm_AI). Author for this delivery: **Utkarsh Raj**. Use the existing `U:\projects\Helm_AI` checkout; `Insurance_UAE` is a different repository.

## Run the prototype

From the repository root, install the existing locked dependencies if needed:

```powershell
npm ci
npm --prefix frontend ci
uv sync --project backend --locked --group dev
```

Keep these in separate terminals:

```powershell
# API: explicitly isolated SQLite database and local encryption key under .runtime
uv run --project backend python backend/scripts/uk_test_server.py
```

```powershell
# Synthetic delayed insurer responses, notifications, expiry cleanup
uv run --project backend python backend/scripts/journey_worker.py
# A single pass is also available with --once
```

```powershell
# Frontend development, normally http://127.0.0.1:5173
npm run dev
```

For the built preview used in verification:

```powershell
$env:VITE_NEXT_CHAT_UI='true'
npm run build
npm --prefix frontend run preview
```

Preview is [http://127.0.0.1:4174](http://127.0.0.1:4174). The API listens on `127.0.0.1:8000`. The demo scripts deliberately override the database and disable Groq; they do not seed or migrate a configured customer database. Do not run multiple API instances or duplicate workers against this scratch SQLite store. A preview serves the last build, so rebuild after frontend edits.

## Entry points

| Route | Purpose |
| --- | --- |
| `/` | Public educational website and refined information assistant |
| `/get-cover/quote` | Canonical shared manual/guided intake and new end-to-end journey |
| `/get-cover/legacy-demo` | Preserved research comparison and downloadable £0 confirmation |
| `/quote-dashboard` | Private quotation dashboard; open its single-use link from the protected demo inbox |
| `/broker.html` | Separate broker sign-in, assigned-case queue and document review |
| `/app/*` | Preserved historical customer experience; existing auth/integrations still apply |

`/research` and `/get-cover/compare` redirect into the canonical intake. The new broker portal is a Vite multipage entry in the same frontend package. This reuses React, icons, auth and styling dependencies without restoring obsolete archived bundles or adding a second package.

## Exercise the customer journey

1. Start a quote. Choose manual or guided mode. Enter fictional people/ages, region, start date, budget/excess/hospital choices, and an explicit essential-benefits answer. A missing answer remains missing; “none” is a distinct answer.
2. Grant the separate health-preference processing permission only if entering those optional/sensitive answers. No diagnoses or identifying documents are needed. All extraction is the controlled fallback; no LLM provider is called.
3. Review and confirm. Recommendations use the confirmed version. Required benefits, strict ceilings and supported eligibility constraints are server-enforced. A what-if is a preview and cannot be requested as a quotation.
4. Select up to three plans. Review the exact fictional profile/plan payload, verify a `.test` email or acknowledged fictional international number with the code in the private demo inbox, then explicitly consent to the named fictional insurers. Broker sharing and notifications are separate choices.
5. Request simulated quotations. The worker processes the persisted request after its delay. Timeout fixtures retry up to three attempts; partial responses are explicit. No actual insurer receives anything.
6. Create a 24- or 48-hour private dashboard link in the demo inbox. Opening the URL clears its fragment; a deliberate **Open private dashboard** action consumes the token. A repeated authorized cookie session can read the case; the original link cannot be exchanged twice.
7. Compare quotations, download PDFs, ask cited questions, stop notifications or contact a broker. Reverify the original demo contact to replace an expired link. Recovery requires access to the protected demo mailbox; it is not real email/WhatsApp ownership verification or cross-device account recovery.

“Contact a broker” also works before intake is complete. It saves a reviewed incomplete case after simulated contact verification and explicit sharing. Selection-triggered cases are created only at the reviewed request boundary. Cases without configured assignment stay private.

## Configure broker access

The portal obtains public auth configuration from `GET /api/config` and uses the existing Supabase client. The API validates the bearer token through Supabase and reads **administrator-controlled** `app_metadata.helm_role = broker`. Client role flags and `user_metadata` do not grant access.

Use an existing approved broker user UUID in the API environment:

```powershell
$env:JOURNEY_DEMO_BROKER_ID='<existing Supabase broker user UUID>'
uv run --project backend python backend/scripts/uk_test_server.py
```

An operator can assign an already-created, consented synthetic case in the isolated database:

```powershell
uv run --project backend python backend/scripts/journey_assign.py --case-id '<case UUID>' --broker-id '<existing Supabase broker UUID>' --expected-version 1
```

Use the current version from the private case response. Assignment is audited and revokes earlier document approvals. There is no public assignment endpoint, fake broker login or role bypass. With Supabase unconfigured, `/broker.html` explains the requirement and the protected API fails closed. The UI fixture in browser tests is explicitly a test fixture, not a real authenticated broker session.

## Broker workflow

- The queue filters by state, expiry urgency and case-reference prefix with pagination. Counts, alerts and every case action are restricted to the authenticated assigned broker and current sharing consent.
- Case details include canonical profile/hard limits/preferences, selected reasons/prices, insurer statuses, verified demo contacts, channel/quiet-hour choices, consent records, saved questions and activity.
- Notes remain broker-private. Human-written customer messages are explicit actions. AI-assisted text belongs to the document review workflow.
- Move `new → triaged → in_progress`. Waiting states can return to progress. Closed cases require a reason and do not reopen implicitly.
- Prepare a source-linked internal summary, information request, insurer request or cover-check draft. These use controlled templates with `provider_called: false` and are labeled simulated AI-assisted drafts.
- Editing creates a new revision and invalidates approvals. Complete the profile/quotation/question/document checklist, then approve the exact content hash, purpose, recipients and profile version.
- **Simulate approved delivery** rechecks assignment, consent, current profile, quotation expiry and exact approval. It writes only the private demo inbox/thread. `submitted` means simulated dispatch; no insurance contract or real submission exists.

Generic broker alerts are persisted in the private broker inbox (`GET /api/journey/broker/inbox`); contacts appear only inside an authorized case. Email/WhatsApp broker alerts and customer notifications have no live transport in this build.

## Storage, retention and migrations

New tables are additive and prefixed `journey_`: session, profile_version, run, contact, case, quote_request, document, quotation, approval, delivery_job and access_grant. Existing historical tables/routes remain separate. Sensitive JSON uses the existing Fernet-backed storage type and a stable server-only key. Never commit `.runtime`, `.env`, database files, encryption keys, raw capabilities or OTPs.

For this demo, the session itself is the guest identity. Consents, notes, messages, flagged questions and redacted audit events live in bounded encrypted aggregate JSON rather than separate generic tables. Limits include 50 profile versions, five saved runs, three selected plans, 20 saved questions, 30 documents, 100 notes/messages and 500 audit events per case. This is the implemented simplification from the larger Phase 0 proposal. Revisit aggregation and queue indexing before real scale.

- Intake expires after 24 hours; the worker removes draft/history/run payloads while preserving minimal version references needed by independently retained cases.
- Explicitly consented case snapshots expire after seven days. Quotations expire within 48 hours. Links last 24/48 hours; dashboard cookies last at most two hours and never outlive their parent grant.
- The protected demo mailbox is bounded to seven days. OTPs expire after ten minutes and allow at most five guesses. Worker cleanup removes expired OTP content.
- Health-processing withdrawal removes sensitive current fields, profile histories, derived runs, cases, documents, approvals and associated delivery/access copies for that journey. Sharing withdrawal denies broker access and cancels/revokes affected future jobs/access.

Existing environments need additive Alembic revisions 0003–0005. Before applying to any non-scratch database, follow its normal backup/review process. The isolated prototype database has already been upgraded; the migration tests cover a fresh database and an existing grant table without `parent_id`.

```powershell
# Run only against your explicitly selected, reviewed development database.
uv run --project backend alembic -c backend/alembic.ini upgrade head
```

The worker claims rows within transactions with database locks and uniqueness constraints. SQLite tests establish application behavior; PostgreSQL concurrency, row-locking and multi-worker behavior are not certified by them. Use a real deployment scheduler/supervisor and monitored retention jobs before changing live scope.

## Checks

```powershell
# Use the in-memory URL for deterministic tests, including a skipped Postgres role check.
$env:DATABASE_URL='sqlite://'
$env:GROQ_API_KEY=''
uv run --project backend pytest backend/tests -q
uv run --project backend ruff check backend/app backend/tests backend/scripts
npm --prefix frontend run lint:uk
npm --prefix frontend test
npm run build
npm run test:uk
npm run test:e2e
```

Run the two browser suites sequentially: their default artifact directories overlap. `npm --prefix frontend run build:production` must still exit unsuccessfully. Actual counts and known exceptions are recorded in [JOURNEY_PROGRESS.md](JOURNEY_PROGRESS.md).

## Live work still outside this delivery

No real insurer, payment, email, WhatsApp, policy issuance, medical underwriting or regulated advice is implemented. A live WhatsApp setup requires business onboarding, opt-in proof, reviewed/provider-approved templates, customer-service-window enforcement, delivery webhooks and real verified destinations. Email needs a configured authenticated transport and real verification/recovery; neither is simulated into a live service here.

LLM extraction/drafting remains the deterministic fallback. Adding a provider requires explicit scope approval, data minimization, per-message consent and tests of invalid/outage responses; outgoing generated prose must retain exact-version human approval. Other launch blockers include regulatory/business placeholders, approved product documents, historical migration, privacy/security/legal review, real broker identity setup, PostgreSQL concurrency, operational monitoring/backups, physical mobile devices and screen-reader testing. The production guard remains enabled.

## Shared repository practice

Fetch/pull before starting, preserve local/collaborator edits, validate the relevant change, commit substantive checkpoints as Utkarsh Raj, fetch/integrate again and push. Never force-push or overwrite a friend's work. The current request delivered 18 implementation commits plus the earlier Phase 0 plan; see the actual ledger in the progress report.
