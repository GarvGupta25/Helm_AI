# Helm AI customer website

Helm AI helps UAE residents discover, compare, purchase and manage individual health insurance. Plans, providers, payments and policies in this repository are fictional demonstration data.

## Main-site pages

- Home and the public Helm assistant; About; Our Partners; Popular Schemes and scheme details.
- UAE newcomer guide and topic pages; How It Works; FAQ; Claims Explained; Contact; privacy, terms and disclaimer.
- Sign in, sign up, account recovery and password reset.
- Customer overview, saved profile, intake/conversation, quote comparison and application confirmation.
- Customer marketplace quotations and activation progress.
- Customer policies, coverage, documents, claims/status/appeals, servicing, payment schedules/receipts, nearby-care map and Ask Helm.

Customer requests for broker review, provider quotations and claim status continue to use the same backend. Their professional processing portals are preserved separately under archive/.

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

Keep the same backend auth, models, API contracts, Supabase schema/RLS and migrations. No database reset, seeding or migration command is required for the frontend split. The existing scripts/start-prototype.ps1 remains pending an ownership decision; it was not run during this task.

Backend environment variable names and historical full-stack setup details are preserved in [the original README](archive/_original_copies/README.md). Do not copy server secrets to frontend configuration. The existing frontend API helper obtains public Supabase configuration from GET /api/config and continues using the existing auth/session implementation.

## Checks

```powershell
npm run build
npm run check
npm --prefix frontend exec -- tsc --noEmit
npm run test:e2e
python archive/verify_preservation.py
```

The browser suite starts a Vite development server and uses deterministic API boundaries; it does not demonstrate a live insurer transaction. Real API/database integrations and device-specific behavior need their existing integration/device checks. No ESLint/Vitest configuration exists in this revision.

archive/ is outside active TypeScript source/test roots, ignored by Vite's watcher, excluded from Tailwind source scanning and ignored by the main Playwright suite. All active customer source remains compiled and checked.

## Review and restoration

The safety tag is backup-before-split-20261022. Review `git diff --stat main..cleanup/split-main-site`. The archive contains exact inverse move commands in restore.sh, which were generated but not executed. With a clean tree, `git switch main` returns to the original checkout; for a separate original-state branch use `git switch -c restore/before-split backup-before-split-20261022`. Detailed selective restoration instructions preserve current files before replacing any original.

See [archive/VERIFICATION.md](archive/VERIFICATION.md) for the completed preservation/build/browser checks and remaining decisions.
