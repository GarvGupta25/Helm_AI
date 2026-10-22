# Group dependencies

All backend endpoints remain in their existing files. No backend, migrations, API contracts or auth helpers were changed. Environment variables are listed by NAME ONLY.

## broker-workspace

- Moves: 3. Copies: 15.
- Purpose, entry files, original routes, exact API templates and standalone checklist: [broker-workspace/README.md](broker-workspace/README.md).

- Runtime packages: react, react-dom, react-router-dom, @tanstack/react-query, @supabase/supabase-js; lucide-react for broker/claim review.
- Build packages: typescript, vite, @vitejs/plugin-react, tailwindcss, @tailwindcss/vite, and existing React type packages. Browser tests: @playwright/test. Original package/lockfiles are copied as reference; no dependency removals.
- Environment: existing template names VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY. Preserved API helper actually reads public auth configuration from /api/config. Separate portals need same-origin /api proxy and allowed frontend origin; a VITE_API_BASE_URL helper is not implemented. Server configuration and server secrets stay in the existing backend.
- Host APIs used by broker-workspace: GET /api/config; GET /api/me/access; existing Supabase Auth/session.
- Copied shared/runtime/tooling files:
  - `frontend/src/api.ts` -> `archive/broker-workspace/frontend/src/api.ts`
  - `frontend/src/Feedback.tsx` -> `archive/broker-workspace/frontend/src/Feedback.tsx`
  - `frontend/src/styles.css` -> `archive/broker-workspace/frontend/src/styles.css`
  - `frontend/src/foundation.css` -> `archive/broker-workspace/frontend/src/foundation.css`
  - `frontend/src/vite-env.d.ts` -> `archive/broker-workspace/frontend/src/vite-env.d.ts`
  - `frontend/src/marketing/tokens.css` -> `archive/broker-workspace/frontend/src/marketing/tokens.css`
  - `frontend/index.html` -> `archive/broker-workspace/frontend/index.html`
  - `frontend/package.json` -> `archive/broker-workspace/frontend/package.json`
  - `frontend/package-lock.json` -> `archive/broker-workspace/frontend/package-lock.json`
  - `frontend/tsconfig.json` -> `archive/broker-workspace/frontend/tsconfig.json`
  - `frontend/vite.config.ts` -> `archive/broker-workspace/frontend/vite.config.ts`
  - `package.json` -> `archive/broker-workspace/package.json`
  - `package-lock.json` -> `archive/broker-workspace/package-lock.json`
  - `playwright.config.ts` -> `archive/broker-workspace/playwright.config.ts`
  - `tests/e2e/support.ts` -> `archive/broker-workspace/tests/e2e/support.ts`

- APIs used by broker-workspace (kept in backend; methods/source locations in AUDIT.md):
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



## provider-workspace

- Moves: 8. Copies: 15.
- Purpose, entry files, original routes, exact API templates and standalone checklist: [provider-workspace/README.md](provider-workspace/README.md).

- Runtime packages: react, react-dom, react-router-dom, @tanstack/react-query, @supabase/supabase-js; lucide-react for broker/claim review.
- Build packages: typescript, vite, @vitejs/plugin-react, tailwindcss, @tailwindcss/vite, and existing React type packages. Browser tests: @playwright/test. Original package/lockfiles are copied as reference; no dependency removals.
- Environment: existing template names VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY. Preserved API helper actually reads public auth configuration from /api/config. Separate portals need same-origin /api proxy and allowed frontend origin; a VITE_API_BASE_URL helper is not implemented. Server configuration and server secrets stay in the existing backend.
- Host APIs used by provider-workspace: GET /api/config; GET /api/me/access; existing Supabase Auth/session.
- Copied shared/runtime/tooling files:
  - `frontend/src/api.ts` -> `archive/provider-workspace/frontend/src/api.ts`
  - `frontend/src/Feedback.tsx` -> `archive/provider-workspace/frontend/src/Feedback.tsx`
  - `frontend/src/styles.css` -> `archive/provider-workspace/frontend/src/styles.css`
  - `frontend/src/foundation.css` -> `archive/provider-workspace/frontend/src/foundation.css`
  - `frontend/src/vite-env.d.ts` -> `archive/provider-workspace/frontend/src/vite-env.d.ts`
  - `frontend/src/marketing/tokens.css` -> `archive/provider-workspace/frontend/src/marketing/tokens.css`
  - `frontend/index.html` -> `archive/provider-workspace/frontend/index.html`
  - `frontend/package.json` -> `archive/provider-workspace/frontend/package.json`
  - `frontend/package-lock.json` -> `archive/provider-workspace/frontend/package-lock.json`
  - `frontend/tsconfig.json` -> `archive/provider-workspace/frontend/tsconfig.json`
  - `frontend/vite.config.ts` -> `archive/provider-workspace/frontend/vite.config.ts`
  - `package.json` -> `archive/provider-workspace/package.json`
  - `package-lock.json` -> `archive/provider-workspace/package-lock.json`
  - `playwright.config.ts` -> `archive/provider-workspace/playwright.config.ts`
  - `tests/e2e/support.ts` -> `archive/provider-workspace/tests/e2e/support.ts`

- APIs used by provider-workspace (kept in backend; methods/source locations in AUDIT.md):
  - `/api/me/access`
  - `/api/provider/applications`
  - `/api/provider/applications/${applicationId}/assistant`
  - `/api/provider/applications/${applicationId}/quote`
  - `/api/provider/policies`
  - `/api/provider/policies/${policy.id}/discontinue`
  - `/api/provider/policies/${policyId}/flags`
  - `/api/provider/policies/${policyId}/payments`
  - `/api/provider/policies/${quote.id}/start`
  - `/api/provider/quotations`
  - `/api/provider/quotations/${quote.id}/accept`



## claim-review

- Moves: 3. Copies: 15.
- Purpose, entry files, original routes, exact API templates and standalone checklist: [claim-review/README.md](claim-review/README.md).

- Runtime packages: react, react-dom, react-router-dom, @tanstack/react-query, @supabase/supabase-js; lucide-react for broker/claim review.
- Build packages: typescript, vite, @vitejs/plugin-react, tailwindcss, @tailwindcss/vite, and existing React type packages. Browser tests: @playwright/test. Original package/lockfiles are copied as reference; no dependency removals.
- Environment: existing template names VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY. Preserved API helper actually reads public auth configuration from /api/config. Separate portals need same-origin /api proxy and allowed frontend origin; a VITE_API_BASE_URL helper is not implemented. Server configuration and server secrets stay in the existing backend.
- Host APIs used by claim-review: GET /api/config; GET /api/me/access; existing Supabase Auth/session.
- Copied shared/runtime/tooling files:
  - `frontend/src/api.ts` -> `archive/claim-review/frontend/src/api.ts`
  - `frontend/src/Feedback.tsx` -> `archive/claim-review/frontend/src/Feedback.tsx`
  - `frontend/src/styles.css` -> `archive/claim-review/frontend/src/styles.css`
  - `frontend/src/foundation.css` -> `archive/claim-review/frontend/src/foundation.css`
  - `frontend/src/vite-env.d.ts` -> `archive/claim-review/frontend/src/vite-env.d.ts`
  - `frontend/src/marketing/tokens.css` -> `archive/claim-review/frontend/src/marketing/tokens.css`
  - `frontend/index.html` -> `archive/claim-review/frontend/index.html`
  - `frontend/package.json` -> `archive/claim-review/frontend/package.json`
  - `frontend/package-lock.json` -> `archive/claim-review/frontend/package-lock.json`
  - `frontend/tsconfig.json` -> `archive/claim-review/frontend/tsconfig.json`
  - `frontend/vite.config.ts` -> `archive/claim-review/frontend/vite.config.ts`
  - `package.json` -> `archive/claim-review/package.json`
  - `package-lock.json` -> `archive/claim-review/package-lock.json`
  - `playwright.config.ts` -> `archive/claim-review/playwright.config.ts`
  - `tests/e2e/support.ts` -> `archive/claim-review/tests/e2e/support.ts`

- APIs used by claim-review (kept in backend; methods/source locations in AUDIT.md):
  - `/api/broker/claims`
  - `/api/broker/claims/${claim.id}/appeal-review`
  - `/api/broker/claims/${claim.id}/review`
  - `/api/broker/claims/${claimId.trim()}/replay`
  - `/api/broker/claims/${claimId}/documents/${documentId}/original`
  - `/api/broker/claims/analytics`
  - `/api/broker/claims/observability`
  - `/api/broker/claims/on-call-shifts`
  - `/api/broker/claims/quality-samples`
  - `/api/broker/claims/quality-samples/${id}/review`
  - `/api/broker/claims/rules`
  - `/api/broker/claims/rules/${kind}`



## _unused

- Moves: 3. Copies: 0.
- Purpose, entry files, original routes, exact API templates and standalone checklist: [_unused/README.md](_unused/README.md).

- Packages: react for the hook; canonical customer CalculationStepper.tsx if restoring its compatibility shim. Lottie asset is data. No endpoints or environment reads.



## Main-site portal URL names

VITE_BROKER_PORTAL_URL, VITE_PROVIDER_PORTAL_URL and VITE_STAFF_PORTAL_URL are optional blank entries added to frontend/.env.example only. Broker/provider/staff/admin or unknown non-member accounts never load customer pages while the authoritative access check is pending, failed or identifies a professional account. No backend roles or auth contracts are changed. HTTP/HTTPS absolute configured addresses become portal links; missing/invalid addresses produce plain guidance and sign-out.

## Shared style details

Whole original stylesheets were copied before edits. The main stylesheet retained .broker-approved because MarketplaceJourney uses it for customer quotation status, .claim-flag because customer claim cards use it, and .provider-map for customer nearby care. Only selectors with professional ownership and no active customer reference were removed after their originals were archived. Archive scanning is disabled for Tailwind; active customer source remains included.

## Package suggestions only

No package is proven exclusive to the archived groups. Leaflet and @types/leaflet remain necessary for the customer nearby-care map; @lottiefiles/dotlottie-web remains necessary for the public assistant; UI/auth/query/build/test packages are shared. Keep package.json and both lockfiles unchanged. There is no existing ESLint or Vitest setup to edit; TypeScript and Playwright are the current frontend checks.

## Needs my decision

Both docs fixture-tour JSON reports and scripts/start-prototype.ps1 stay in place. The reports may be historical deliverables; the launcher combines main-site development services and backend seeders. Nothing under backend/ is moved, including professional APIs, fixtures, scripts, tests and generated metadata. Supabase schema/RLS/migrations remain untouched.
