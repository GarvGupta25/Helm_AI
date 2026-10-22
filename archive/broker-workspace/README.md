# broker-workspace

## Purpose

Assigned-member recommendation review, marketplace quotation checkpoints, policy reassessment and servicing-appeal review.

## Preserved entry

frontend/src/Broker.tsx: BrokerWorkspace at /app/broker; frontend/src/MarketplaceBrokerPanel.tsx is its child.

Original files are listed in ../MANIFEST.md and are byte-preserved at move time. No backend files or environment files are copied here.

## Shared files and packages

Copied, not moved: frontend/src/api.ts (Config, Supabase session/auth setup, API helpers), Feedback.tsx, styles.css, foundation.css, vite-env.d.ts and marketing/tokens.css. The whole original stylesheets include professional rules and shared customer primitives. Copies of frontend/package.json, lockfile, tsconfig.json, vite.config.ts and index.html provide the original toolchain. Root package/lockfile, playwright.config.ts and tests/e2e/support.ts support the preserved browser test. They are reference copies from before the split, not new deployment settings.

Runtime: React, React DOM, React Router, TanStack Query and Supabase JS; broker/claim review also use lucide-react. Shared styles require Tailwind CSS, @tailwindcss/vite, Vite, @vitejs/plugin-react, TypeScript and the existing type packages. Browser tests require @playwright/test. No dependency is removed from the consumer site. The copied package manifests intentionally retain the complete original dependency set.

## Environment names and API connection

No browser environment variable is read by these preserved modules today. Existing example names are VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY, but configureAuth currently obtains its public configuration from GET /api/config. Auth uses the existing Supabase session; do not copy server secrets or put backend environment values into frontend bundles.

API URLs are relative /api/... paths. For local development the copied Vite config proxies /api and /health to the existing backend on port 8000. For a separate deployed portal configure a same-origin reverse proxy or deliberately adapt the API helper later; VITE_API_BASE_URL is not currently implemented. Backend ALLOWED_ORIGINS must permit the portal origin when required; this task has not changed backend configuration. Portal-link variable names on the consumer site are VITE_BROKER_PORTAL_URL, VITE_PROVIDER_PORTAL_URL and VITE_STAFF_PORTAL_URL; no values are bundled in the archive.

## Existing API endpoints

GET /api/config and GET /api/me/access are shared host dependencies. Modules use the following endpoint templates; see ../AUDIT.md for their exact registered HTTP methods and backend source locations:

- `/api/broker/appeals`
- `/api/broker/appeals/${item.id}/review`
- `/api/broker/cases/${selectedApplicant}`
- `/api/broker/marketplace/applications`
- `/api/broker/marketplace/applications/${selected}`
- `/api/broker/marketplace/applications/${selected}/checkpoint-2`
- `/api/broker/marketplace/provider-performance`
- `/api/broker/reassessments`
- `/api/broker/reassessments/${item.id}/review`
- `/api/broker/recommendations`
- `/api/broker/recommendations/${item.id}/review`
- `/api/broker/worklist`

## Standalone setup checklist

1. Create a new repository.
2. Copy this group's contents, preserving frontend/ and tests/ paths. Keep README.md and consult ../MANIFEST.md for copied dependencies.
3. Add or adapt package.json/Vite configuration using the included reference copies. Create frontend/src/main.tsx: this is intentionally not copied from the monorepo because it imports customer pages and the other portals. Mount React, BrowserRouter and QueryClientProvider; load foundation.css, marketing/tokens.css and styles.css in the original order. Fetch /api/config, call the unchanged configureAuth, and use existing Supabase auth/session handling. Then `npm ci` at the root and in frontend/, `npm --prefix frontend run build`, and `npm --prefix frontend run dev`. These commands become usable once that entry exists.
4. Set the portal's environment/proxy configuration with names only as described above; never copy real environment files.
5. Point /api at the existing backend and keep all request/response contracts unchanged.
6. Add an auth/role guard requiring `broker` using GET /api/me/access and the existing authenticated backend. Preserve loading/error behavior and sign-out. Backend role, ownership and organisation checks remain authoritative.

The archived test retains original monorepo Login/Shell assumptions, API mocks and paths. Supply compatible /login and route mounts in the new bootstrap before running it. It is excluded from the main site's current test suite. This folder is a preservation/extraction kit, not an already deployed standalone app.

## Cross-portal links

Broker.tsx links to /app and /app/quotes/{id}; those customer pages remain in the consumer repo. Set a deliberate consumer-site URL when extracting rather than moving those pages here. Claim review is preserved separately in ../claim-review/.
