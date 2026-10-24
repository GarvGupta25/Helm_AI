# Helm AI — UK private medical cover demonstration

The latest [chat and member-account update](docs/CHAT_AND_MEMBER_UPDATE.md) adds a modern document-upload panel, saved response feedback/issue reports in a separate database, browser read aloud, English-only chat/intake, and two persistent demo member landing pages. Open `/login` to try the new-member and policyholder accounts, or `/signup` to create a fictional local account. The isolated demo API enables these member-only accounts; existing Supabase professional authentication remains separate.

For a detailed explanation of the project, delivered features, architecture, setup, shared-repository workflow, and remaining work, read [Project overview and current build status](PROJECT_OVERVIEW.md).

The intake-to-broker demo is implemented in 18 development checkpoints. Read the [journey progress and verification report](docs/roadmap/JOURNEY_PROGRESS.md), [architecture plan](docs/roadmap/JOURNEY_PLAN.md), and [operator runbook](docs/roadmap/JOURNEY_RUNBOOK.md). The owner authorized continuing phases without repeated approval pauses; outgoing AI-assisted drafts still require in-product human approval.

The new public site explains UK private medical cover and compares fictional plans with server-calculated, tax-inclusive prices. It includes a structured quote demo and a reviewed information assistant. No money is collected or insurance contract created. This is **not ready for a real UK insurance launch**.

Phase checkpoints are committed on `main`. See [phase reports](docs/uk/PHASE_REPORTS.md), [launch blockers](docs/uk/LAUNCH_READINESS.md), [changelog](docs/uk/CHANGELOG_UK.md) and [measured evidence](docs/uk/PERFORMANCE_ACCESSIBILITY_REPORT.md). The historical customer workflows and professional archives remain preserved and require a separate safe domain/data migration. The historical-term inventory is nonzero; a passing demo build does not mean the whole repository is localised.

### New research and public chat features

The normal **Get a quote** journey at `/get-cover/quote` now starts with a shared manual/guided intake. Confirm answers, compare up to three deterministic fictional recommendations, ask cited policy questions, verify a fictional contact, and review named sharing consent before requesting simulated quotations. A private 24/48-hour link opens received quotations, PDF downloads, policy Q&A and broker messages. The prior research comparison and £0 confirmation remain available at `/get-cover/legacy-demo`; `/research` and `/get-cover/compare` lead to the canonical intake.

The new separate `/broker.html` entry uses the existing Supabase authentication and broker role. Its queue exposes only assigned cases with active sharing consent. Brokers can prepare, edit, approve and simulate delivery of exact document revisions. It stays closed when authentication is not configured. Legacy professional archives remain preserved.

The redesigned public widget adds streaming/Stop, attachment processing, voice feature detection, session controls, English-only controls and dark mode. It is enabled by default in development and built previews. For an explicit preview/QA setting, use `$env:VITE_NEXT_CHAT_UI='true'` **before** building. Set it to `false` to retain the legacy panel. See [design notes and verification limits](docs/chatbot-design-notes.md). Optional provider calls need credentials and explicit consent; learned ranking remains disabled.

### Run the isolated UK demo

```powershell
npm ci
npm --prefix frontend ci
uv sync --project backend --locked --group dev
# Terminal 1: explicitly uses a scratch SQLite database, never your configured database
uv run --project backend python backend/scripts/uk_test_server.py
# Terminal 2: delayed insurer replies, private demo notifications and retention
uv run --project backend python backend/scripts/journey_worker.py
# Terminal 3
npm run dev
```

The public pages work without an API; the quote and assistant require the test API. Build with `npm run build`. Run `npm run test:uk` after building; the browser suite uses the production preview and an isolated API. `npm --prefix frontend run build:production` intentionally fails while live-release blockers remain. Do not deploy the legacy authenticated workflows as a completed UK migration.

## Main-site pages

- Home and the public Helm assistant; About; Our Partners; Popular Schemes and scheme details.
- UK newcomer guide, underwriting, cover categories, FAQs, glossary, fictional care finder and draft legal/support pages.
- Sign in, sign up, account recovery and password reset.
- Customer overview, saved profile, intake/conversation, quote comparison and application confirmation.
- Customer marketplace quotations and activation progress.
- Customer policies, coverage, documents, claims/status/appeals, servicing, payment schedules/receipts, nearby-care map and Ask Helm.

Historical customer requests for broker review, provider quotations and claim status continue to use the same backend. Those older professional portals remain in archive/. The new journey broker portal at /broker.html is additive and uses separate journey tables.

## Preserved professional portals

Broker Workspace, Provider Workspace, broker Claim Review and operational tools are archived with their dedicated tests. See [archive/README.md](archive/README.md), [MANIFEST.md](archive/MANIFEST.md) and [DEPENDENCIES.md](archive/DEPENDENCIES.md). Each group has an extraction README and shared dependency/config copies. No backend or database code was moved.

Professional accounts signing into this customer website receive portal guidance and sign-out. Configure these optional names in the frontend deployment (blank examples in frontend/.env.example):

- VITE_BROKER_PORTAL_URL
- VITE_PROVIDER_PORTAL_URL
- VITE_STAFF_PORTAL_URL

Use an absolute HTTP/HTTPS portal URL. With no valid URL configured, the site shows guidance without a broken link. Backend authorization and role contracts remain unchanged.

## Development

Requirements: Node.js 22 or compatible, Python 3.12 for the existing backend, uv, and the project's existing local/hosted Supabase setup. Database, real environment files and credentials are configured separately and are not modified by this repository split.

```powershell
npm ci
npm --prefix frontend ci
npm run dev -- --port 5174
```

The frontend proxies /api and /health to the existing API on port 8000. Start the backend and worker using your established configuration:

```powershell
# First terminal, repository root
uv run --project backend uvicorn app.main:app --host 127.0.0.1 --port 8000

# Second terminal
uv run --project backend python -m app.worker
```

Keep the same backend auth, models, API contracts, Supabase schema/RLS and migrations. The earlier frontend split required no database reset. The new journey adds Alembic revisions 0003–0005; follow the journey runbook for an existing environment. The isolated test server creates only scratch demo tables. The existing scripts/start-prototype.ps1 remains pending an ownership decision; it was not run during this task.

Backend environment variable names and historical full-stack setup details are preserved in [the original README](archive/_original_copies/README.md). Do not copy server secrets to frontend configuration. The existing frontend API helper obtains public Supabase configuration from GET /api/config and continues using the existing auth/session implementation.

## Checks

```powershell
npm run build
npm run check
npm --prefix frontend exec -- tsc --noEmit
npm run test:e2e
python archive/verify_preservation.py
```

The browser suite starts a Vite development server and uses deterministic API boundaries; it does not demonstrate a live insurer transaction. Real API/database integrations and device-specific behavior need their existing integration/device checks. Scoped ESLint and Vitest commands are available in `frontend/package.json`; see the project overview for the current verification commands.

archive/ is outside active TypeScript source/test roots, ignored by Vite's watcher, excluded from Tailwind source scanning and ignored by the main Playwright suite. All active customer source remains compiled and checked.

## Review and restoration

The safety tag is backup-before-split-20261022. Review `git diff --stat main..cleanup/split-main-site`. The archive contains exact inverse move commands in restore.sh, which were generated but not executed. With a clean tree, `git switch main` returns to the original checkout; for a separate original-state branch use `git switch -c restore/before-split backup-before-split-20261022`. Detailed selective restoration instructions preserve current files before replacing any original.

See [archive/VERIFICATION.md](archive/VERIFICATION.md) for the completed preservation/build/browser checks and remaining decisions.
