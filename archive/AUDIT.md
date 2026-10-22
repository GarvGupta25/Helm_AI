# Proposed main-site split audit

Status: PHASE 1 ONLY — classification approval required before Phase 2. No source files have been edited, moved, copied, or deleted. This new audit document is the sole working-tree addition.

## Safety and scope

- Working folder: `U:/projects/Helm_AI-main/Helm_AI-main`.
- Upstream: `https://github.com/GarvGupta25/Helm_AI.git`, branch `main`.
- Latest upstream main verified on 2026-10-22: `8140750cf7fdae91443f9fe59938f41f03fb57b7` (2026-10-20, Fix claim attachment uploads when OCR is unavailable).
- The supplied folder had no Git metadata. Git was initialized, upstream history fetched, `main` pointed at upstream, and the index populated with `git read-tree HEAD`. These operations did not write checkout source files. The resulting working tree was clean and matched upstream.
- Safety tag: `backup-before-split-20261022` on `main`. Working branch: `cleanup/split-main-site`. No push or merge.
- Baseline: 187 tracked files. All remain at their original paths. Backend (77 files), Supabase (16 files), migrations, API contracts, and environment files are frozen.
- Evidence is static source/import/router/test inspection. No application, seeder, database command, startup script, build, or test was run in Phase 1.
- The client date, 2026-10-22, is used for the safety tag.

## Classification summary

| Bucket | Scope / group | Baseline files | Proposed handling |
| --- | --- | --- | --- |
| A — KEEP | Marketing pages, legal/help pages, homepage assistant, auth/customer flows and customer tests | 56 | Keep their routes, components, styles and assets. |
| B — MOVE | broker-workspace | 3 | Broker workspace, marketplace review panel, dedicated browser test. |
| B — MOVE | provider-workspace | 8 | Provider workspace and six sibling modules/types, dedicated browser test. |
| B — MOVE | claim-review | 3 | Broker claim review, operational/rule tools, dedicated browser test. |
| C — MOVE | _unused | 3 | Unreferenced re-export, unused hook and unused assistant asset; detailed evidence below. |
| D — SHARED | API/auth, shell/router, feedback, global styles, test support, tooling and protected backend/database files | 111 | Keep originals. Copy only dashboard-required frontend/tooling/support dependencies after approval. |
| E — UNSURE | Fixture reports and prototype startup script | 3 | Leave in place until an explicit decision. |

Counts apply to baseline files only; shared copies, original snapshots and new archive documentation will be additional files. No standalone staff-console or admin frontend exists in this revision. ClaimOperations contains rule editing, operational metrics, quality audits and replay; it belongs to claim-review. Senior-broker escalation is part of ClaimReview. Customer claim submission/status/appeals remain in Shopping.tsx and ClaimAdvocate.tsx.

## Every frontend route

Router: `frontend/src/main.tsx`. All ordinary pages also inherit `GET /api/config`; authenticated Shell routes additionally use `GET /api/me/access`. Authentication talks to Supabase Auth through the existing client, not a new Helm backend login endpoint. Entries below describe current behavior, not completed changes.

| Path | Element | Bucket | Current backend use / behavior |
| --- | --- | --- | --- |
| / | HomePage | A | GET /api/public/marketplace-plans; GET /api/public/marketplace-partners; assistant via MarketingLayout |
| /about | AboutPage | A | Static; assistant via MarketingLayout |
| /partners | PartnersPage | A | GET /api/public/marketplace-partners |
| /plans | PlansPage | A | GET /api/public/marketplace-plans; existing popular/best-scheme catalogue |
| /plans/:planId | PlanDetailPage | A | GET /api/public/marketplace-plans |
| /guide | GuidePage | A | Static UAE newcomer guide |
| /guide/:topicSlug | GuideTopicPage | A | Static topic from route parameter |
| /how-it-works | HowItWorksPage | A | Static |
| /faq | FaqPage | A | Static |
| /claims-explained | ClaimsExplainedPage | A | Static customer help, not internal claim review |
| /contact | ContactPage | A | Local form state only; no backend submission call found |
| /legal/privacy | PrivacyPage | A | Static |
| /legal/terms | TermsPage | A | Static |
| /legal/disclaimer | DisclaimerPage | A | Static |
| /login | Login (inline main.tsx) | A behavior in D file | Supabase sign-in, sign-up, recovery, updateUser; /login?recovery=1 uses same route |
| /app (index) | Dashboard (Shopping.tsx) | A | GET /api/policies, /api/cases, /api/me/profile, /api/marketplace/applications, /api/marketplace/notifications, /api/marketplace/policies; POST /api/cases, /api/policies/import |
| /app/intake/:caseId | Intake (Shopping.tsx) | A | GET/PATCH /api/me/profile; profile/document/voice/conversation APIs via children |
| /app/quotes/:quoteId | QuotePage (Shopping.tsx) | A | GET /api/quotes/{quote_id}, /api/sources; POST /api/applications/prepare; GET quote PDF; nearby-care map |
| /app/applications/:applicationId | ApplicationPage (Shopping.tsx) | A | GET /api/applications/{application_id}; POST /api/applications/{application_id}/submit |
| /app/broker | BrokerWorkspace | B / broker-workspace | /api/broker/recommendations, appeals, reassessments, worklist, cases; marketplace broker APIs |
| /app/broker/claims | ClaimReview | B / claim-review | /api/broker/claims/* including review, originals, operational rules and quality audits |
| /app/marketplace/:caseId | MarketplaceJourney | A | GET recommendations/quotations; POST consent/quotation select; keep customer responses and activation status |
| /app/policies/:policyId | PolicyPage (Shopping.tsx) | A | Customer policy, claim-intake/status/evidence/appeals, reassessment, updates, payments, nearby care and Ask Helm APIs; complete file map below |
| /broker/claims | Navigate alias | B / claim-review | Redirects to /app/broker/claims; archive this route registration with main.tsx original snapshot |
| /provider (index) | ProviderWorkspace inside Shell | B / provider-workspace | GET /api/me/access plus /api/provider/* |
| * | Navigate fallback to / | A behavior in D file | No direct API; retain fallback |

`/app` and `/provider` parent routes mount the shared Shell; nested routes above include their index elements. Shell also reads `/api/policies` for PoliciesLink and member-only `/api/marketplace/notifications`. Signup/password reset are modes of Login, not separate missing routes. Homepage chat is mounted by MarketingLayout, so it also appears on the other marketing routes.

## Navigation and mixed-file repair scope (after approval)

| File(s) | Bucket | Required handling |
| --- | --- | --- |
| frontend/src/main.tsx | D | Lazy imports and route registrations for BrokerWorkspace, ClaimReview, ProviderWorkspace; /broker/claims alias; internal sidebar links; provider redirect from /app; mixed Shell styling/copy. Preserve the entire original before any edit. Keep Login auth calls and customer routes/API calls. |
| frontend/src/styles.css | D | Broker-only selectors, provider-grid selectors and broker claim review/original-preview rules coexist with customer styles. Copy the entire original before edits. Shared selector lists such as .servicing-layout,.broker-grid must retain the customer branch. |
| frontend/src/foundation.css | D | Global responsive rules include customer and professional selectors in the same rule. Preserve the original before editing any mixed selector rule. |
| frontend/src/marketing/components/MarketingHeader.tsx + MarketingFooter.tsx | A | All current navigation targets are public/customer paths. No broker/provider links to remove here. Do not edit without a concrete need. |
| frontend/src/Shopping.tsx, Conversation.tsx, MarketplaceJourney.tsx | A | Member requests for broker review, approval waiting state, claim status, appeals, provider responses and progress are customer functionality. They stay even though they mention professional roles. |
| README.md | D | Shared product, customer, internal-workspace and setup documentation. Preserve whole original before moving or revising internal sections; copy relevant documentation into group READMEs after approval. No credential values will be repeated in archive docs. |
| frontend/.env.example | D / protected template | Phase 3 explicitly permits adding portal variable names to this template only; archive the original before editing. Never read/copy/change real .env files. Suggested new names: VITE_BROKER_PORTAL_URL, VITE_PROVIDER_PORTAL_URL. Staff portal mapping is not present in current role contracts. |
| frontend/tsconfig.json, frontend/vite.config.ts, playwright.config.ts, .github/workflows/checks.yml | D | Review archive exclusion boundaries after moves. TypeScript currently includes frontend/src and vite.config.ts; Vite root is frontend; Playwright testDir is tests/e2e. Archive at repo root is already outside those source/test roots. No ESLint/Vitest config or lint/unit-test script exists. Do not add broad excludes that suppress kept-code errors. |

Professional login behavior to implement only after approval: retain the authoritative `/api/me/access` request and existing Supabase auth helpers; show broker/provider portal guidance in the frontend shell, with URLs supplied by example-variable names above. Do not change backend roles, auth logic, or endpoint contracts. A staff/admin-specific identity cannot be inferred from the current member/broker/provider contract; no invented backend role or portal URL will be added.

## B: complete import and extraction dependency trace

Proposed files below are the real files to move using `git mv`, retaining their original repository-relative paths inside each group. Shared D files remain in place and are copied. Inline test stubs/mock data travel with their test file; no separate dashboard mock-data directory was found.

| Move file | Group | Direct B imports | Direct D imports / config | npm packages | Transitive host dependency |
| --- | --- | --- | --- | --- | --- |
| frontend/src/Broker.tsx | broker-workspace | `frontend/src/MarketplaceBrokerPanel.tsx` | `frontend/src/Feedback.tsx`<br>`frontend/src/api.ts` | `@tanstack/react-query`<br>`lucide-react`<br>`react`<br>`react-router-dom` | All are rendered by main.tsx Shell (D), with styles.css and foundation.css (D). Group needs its own bootstrap/auth shell later. |
| frontend/src/MarketplaceBrokerPanel.tsx | broker-workspace | None | `frontend/src/Feedback.tsx`<br>`frontend/src/api.ts` | `@tanstack/react-query`<br>`lucide-react`<br>`react` | All are rendered by main.tsx Shell (D), with styles.css and foundation.css (D). Group needs its own bootstrap/auth shell later. |
| tests/e2e/broker-marketplace.spec.ts | broker-workspace | None | `tests/e2e/support.ts`<br>`playwright.config.ts` | `@playwright/test` | Browser test also uses the shared Login/Shell behavior and deterministic Supabase/API fixtures. |
| frontend/src/provider/ProviderApplications.tsx | provider-workspace | `frontend/src/provider/types.ts` | `frontend/src/api.ts` | `@tanstack/react-query` | All are rendered by main.tsx Shell (D), with styles.css and foundation.css (D). Group needs its own bootstrap/auth shell later. |
| frontend/src/provider/ProviderFinancialAccounts.tsx | provider-workspace | None | `frontend/src/api.ts` | `@tanstack/react-query` | All are rendered by main.tsx Shell (D), with styles.css and foundation.css (D). Group needs its own bootstrap/auth shell later. |
| frontend/src/provider/ProviderFlagForm.tsx | provider-workspace | None | `frontend/src/api.ts` | `react` | All are rendered by main.tsx Shell (D), with styles.css and foundation.css (D). Group needs its own bootstrap/auth shell later. |
| frontend/src/provider/ProviderPolicies.tsx | provider-workspace | `frontend/src/provider/types.ts` | `frontend/src/Feedback.tsx`<br>`frontend/src/api.ts` | `@tanstack/react-query`<br>`react` | All are rendered by main.tsx Shell (D), with styles.css and foundation.css (D). Group needs its own bootstrap/auth shell later. |
| frontend/src/provider/ProviderQuoteForm.tsx | provider-workspace | None | `frontend/src/api.ts` | `@tanstack/react-query`<br>`react` | All are rendered by main.tsx Shell (D), with styles.css and foundation.css (D). Group needs its own bootstrap/auth shell later. |
| frontend/src/provider/ProviderWorkspace.tsx | provider-workspace | `frontend/src/provider/ProviderApplications.tsx`<br>`frontend/src/provider/ProviderFinancialAccounts.tsx`<br>`frontend/src/provider/ProviderFlagForm.tsx`<br>`frontend/src/provider/ProviderPolicies.tsx`<br>`frontend/src/provider/ProviderQuoteForm.tsx` | `frontend/src/api.ts` | `@tanstack/react-query`<br>`react`<br>`react-router-dom` | All are rendered by main.tsx Shell (D), with styles.css and foundation.css (D). Group needs its own bootstrap/auth shell later. |
| frontend/src/provider/types.ts | provider-workspace | None | None | None | All are rendered by main.tsx Shell (D), with styles.css and foundation.css (D). Group needs its own bootstrap/auth shell later. |
| tests/e2e/provider-workspace.spec.ts | provider-workspace | None | `tests/e2e/support.ts`<br>`playwright.config.ts` | `@playwright/test` | Browser test also uses the shared Login/Shell behavior and deterministic Supabase/API fixtures. |
| frontend/src/broker/ClaimReview.tsx | claim-review | `frontend/src/broker/ClaimOperations.tsx` | `frontend/src/Feedback.tsx`<br>`frontend/src/api.ts` | `@tanstack/react-query`<br>`lucide-react`<br>`react` | All are rendered by main.tsx Shell (D), with styles.css and foundation.css (D). Group needs its own bootstrap/auth shell later. |
| frontend/src/broker/ClaimOperations.tsx | claim-review | None | `frontend/src/api.ts` | `@tanstack/react-query`<br>`react` | All are rendered by main.tsx Shell (D), with styles.css and foundation.css (D). Group needs its own bootstrap/auth shell later. |
| tests/e2e/claim-review.spec.ts | claim-review | None | `tests/e2e/support.ts`<br>`playwright.config.ts` | `@playwright/test` | Browser test also uses the shared Login/Shell behavior and deterministic Supabase/API fixtures. |

Common frontend copies needed by all three dashboard groups: `frontend/src/api.ts`, `frontend/src/Feedback.tsx`, `frontend/src/styles.css`, `frontend/src/foundation.css`, and `frontend/src/vite-env.d.ts`. ClaimOperations itself only directly imports api.ts; its parent ClaimReview supplies the shared feedback/style requirements. Provider types.ts is local to the provider group and moves with it. Each group also needs a COPY of `tests/e2e/support.ts` for its archived browser test and documented package/build/test setup. Main-site package.json files and lockfiles are retained; tooling can be copied as reference/templates without replacing their originals.

Copying the entire main.tsx into a runnable group would drag in customer pages and other groups. Instead, preserve it in `_original_copies/` before edits, record its Shell/Login/router contracts here and in group READMEs, and document a new minimal per-portal bootstrap/role guard. Archive modules will require that bootstrap and package/Vite setup before becoming a standalone app; moving files alone does not make a new deployable portal.

Broker.tsx currently links to `/app`, `/app/quotes/{id}` and quote comparison routes. These are cross-app customer views, not local dependencies to move. Record them in broker-workspace README as integration decisions for the future portal. ProviderWorkspace redirects non-providers to `/app`; record that existing dependency for later standalone adaptation. No cross-app API change is needed.

## Group package, environment and API dependencies

| Group | Runtime packages | Environment / backend contract | Backend APIs to leave in place |
| --- | --- | --- | --- |
| broker-workspace | react, react-dom, react-router-dom, @tanstack/react-query, lucide-react, @supabase/supabase-js; tailwindcss + Vite toolchain for shared CSS | Config from GET /api/config; configureAuth(config); Supabase session from existing auth client; /api relative URLs with Vite proxy. Future portal needs an API-origin/proxy configuration and allowed frontend origin; do not invent a currently supported VITE_API_BASE_URL. | /api/me/access; /api/broker/recommendations*, /appeals*, /reassessments*, /worklist, /cases/*; /api/broker/marketplace/applications*, /provider-performance |
| provider-workspace | react, react-dom, react-router-dom, @tanstack/react-query, @supabase/supabase-js; tailwindcss + Vite toolchain | Same config/session/proxy contract; provider mapping/role stays enforced by backend. Existing example names VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are not read by api.ts: browser auth currently uses /api/config. | /api/me/access; /api/provider/applications*, /quotations*, /policies* |
| claim-review | react, react-dom, react-router-dom (host shell), @tanstack/react-query, lucide-react, @supabase/supabase-js; tailwindcss + Vite toolchain | Same config/session/proxy contract; original document download uses session bearer header. No server secrets should be copied into a frontend group. | /api/me/access; /api/broker/claims and every review/original/analytics/on-call/rules/observability/quality-samples/replay/appeal-review subroute |
| _unused | react for unused hook; CalculationStepper shim would need the retained canonical component if restored; unused Lottie JSON is data only | No direct backend calls or runtime environment reads. | None |

Every dashboard browser test additionally needs `@playwright/test` and `tests/e2e/support.ts`. No npm package is proven exclusive to archived functionality: React, React Router, Query, Supabase, icons and Tailwind are shared; Leaflet is needed by the customer nearby-care map and Lottie by the public assistant. Keep every dependency and lockfile unchanged during this split.

No active frontend `import.meta.env` / `process.env` reads were found. The existing frontend environment-template variable names are documented here as names only. Proposed portal URL variable names are future additions, not existing capabilities. Backend configuration stays with the existing backend; no secrets, backend files, or migrations are copied into the dashboard groups.

## C: proposed unused files and evidence

| File | Evidence | Preservation / caveat |
| --- | --- | --- |
| frontend/src/components/CalculationStepper.tsx | One-line compatibility re-export. No source/test/config import resolves to this shim. Shopping.tsx imports the canonical frontend/src/CalculationStepper.tsx directly. | Move shim only. Keep canonical CalculationStepper.tsx and customer calculation UI. |
| frontend/src/marketing/hooks/useScrollReveal.ts | Only occurrence of useScrollReveal in tracked source is its own definition; no inbound imports or runtime references found. | Move entire hook, preserving its React/IntersectionObserver implementation. |
| frontend/public/assets/helm-assistant.json | No tracked source/config/docs reference to helm-assistant.json. Active ChatbotLauncher explicitly loads /assets/robot.json. | Move this asset only. Keep robot.json and @lottiefiles/dotlottie-web. Static evidence supports archival; preserve the file so it can be restored. |

Import graph cross-check: 69 TypeScript/TSX/CSS source files examined, 66 reachable from main.tsx. The only non-imported source files are the two C modules above and vite-env.d.ts. The latter is D and must stay because TypeScript includes ambient declarations without an import. No additional dead pages/components are proposed.

## E: Needs my decision (leave in place)

| Item | Why uncertain | Safe default |
| --- | --- | --- |
| docs/deliverable/fixture_tour_report.json + docs/fixture_tour_latest.json | Parsed JSON contents are equal, with applicant/profile, preauth, claim, reimbursement, appeal and final-ledger evidence. They may be deliverable/audit fixtures even though the files are duplicates. | Retain both. Decide whether either report belongs in _unused. |
| scripts/start-prototype.ps1 | Mixed local launcher for Supabase, API, worker and frontend. It also invokes backend demo-account/provider seeders and references local environment files. It may remain essential for customer development. | Retain and do not run. Decide whether the prototype launcher should eventually be archived or kept. |

The 77 backend files include generated egg-info, scripts, fixture tours, broker/provider/claim-review tests and seeders. They are deliberately classified D/protected and left untouched even where they look generated or dashboard-only. The explicit backend freeze takes precedence over generic unused-code cleanup.

## Complete frontend page/component/module inventory

| File | Bucket | Top-level components/helpers/types | Local imports |
| --- | --- | --- | --- |
| frontend/src/Broker.tsx | B | Recommendation, Appeal, Reassessment, certaintyLabel, BrokerWorkspace | `frontend/src/Feedback.tsx`<br>`frontend/src/MarketplaceBrokerPanel.tsx`<br>`frontend/src/api.ts` |
| frontend/src/CalculationStepper.tsx | A | CalculationStepper | None |
| frontend/src/ClaimAdvocate.tsx | A | ClaimAdvocate | `frontend/src/api.ts` |
| frontend/src/Conversation.tsx | A | Conversation | `frontend/src/Voice.tsx`<br>`frontend/src/api.ts` |
| frontend/src/CoverageSummary.tsx | A | Plan, coverageSummaryText, CoverageSummary | `frontend/src/Voice.tsx`<br>`frontend/src/api.ts` |
| frontend/src/Feedback.tsx | D | Loading, ErrorView | None |
| frontend/src/FormActions.tsx | A | FormActions | None |
| frontend/src/MarketplaceBrokerPanel.tsx | B | Application, Detail, Performance, MarketplaceBrokerPanel | `frontend/src/Feedback.tsx`<br>`frontend/src/api.ts` |
| frontend/src/MarketplaceJourney.tsx | A | steps, nextSteps, Quotation, Journey, Recommendation, term, QuotationTerms, MarketplaceJourney | `frontend/src/Feedback.tsx`<br>`frontend/src/api.ts` |
| frontend/src/PolicyNotifications.tsx | A | Installment, ServicingEvent, PolicyNotifications | `frontend/src/api.ts` |
| frontend/src/ProfileEditor.tsx | A | extendedGroups, Field, extendedRegistry, ProfileEditor | `frontend/src/FormActions.tsx`<br>`frontend/src/api.ts` |
| frontend/src/Providers.tsx | A | Providers | `frontend/src/api.ts` |
| frontend/src/Shopping.tsx | A | Dashboard, Intake, QuotePage, flatten, ApplicationPage, loadCheckout, ClaimStatusCard, suggestedDocumentType, PolicyPage | `frontend/src/CalculationStepper.tsx`<br>`frontend/src/ClaimAdvocate.tsx`<br>`frontend/src/Conversation.tsx`<br>`frontend/src/CoverageSummary.tsx`<br>`frontend/src/Feedback.tsx`<br>`frontend/src/PolicyNotifications.tsx`<br>`frontend/src/ProfileEditor.tsx`<br>`frontend/src/Providers.tsx`<br>`frontend/src/Voice.tsx`<br>`frontend/src/api.ts` |
| frontend/src/Voice.tsx | A | ReadAloud, VoiceInput | `frontend/src/api.ts` |
| frontend/src/api.ts | D | Config, configureAuth, ApiError, api, post, downloadQuote, aed | None |
| frontend/src/broker/ClaimOperations.tsx | B | ClaimOperations | `frontend/src/api.ts` |
| frontend/src/broker/ClaimReview.tsx | B | ReviewAction, Claim, actionLabels, show, OriginalPreview, ClaimReview | `frontend/src/Feedback.tsx`<br>`frontend/src/api.ts`<br>`frontend/src/broker/ClaimOperations.tsx` |
| frontend/src/components/CalculationStepper.tsx | C | CalculationStepper re-export | `frontend/src/CalculationStepper.tsx` |
| frontend/src/main.tsx | D | HomePage, AboutPage, PartnersPage, PlansPage, PlanDetailPage, GuidePage, GuideTopicPage, HowItWorksPage, FaqPage, ClaimsExplainedPage, ContactPage, PrivacyPage, TermsPage, DisclaimerPage, Dashboard, Intake, QuotePage, ApplicationPage, PolicyPage, BrokerWorkspace, ClaimReview, ProviderWorkspace, MarketplaceJourney, client, Brand, Login, PoliciesLink, Shell, MessageIcon, FileTextIcon, App | `frontend/src/Broker.tsx`<br>`frontend/src/Feedback.tsx`<br>`frontend/src/MarketplaceJourney.tsx`<br>`frontend/src/Shopping.tsx`<br>`frontend/src/api.ts`<br>`frontend/src/broker/ClaimReview.tsx`<br>`frontend/src/foundation.css`<br>`frontend/src/marketing/components/MarketingLayout.tsx`<br>`frontend/src/marketing/pages/AboutPage.tsx`<br>`frontend/src/marketing/pages/ClaimsExplainedPage.tsx`<br>`frontend/src/marketing/pages/ContactPage.tsx`<br>`frontend/src/marketing/pages/DisclaimerPage.tsx`<br>`frontend/src/marketing/pages/FaqPage.tsx`<br>`frontend/src/marketing/pages/GuidePage.tsx`<br>`frontend/src/marketing/pages/GuideTopicPage.tsx`<br>`frontend/src/marketing/pages/HomePage.tsx`<br>`frontend/src/marketing/pages/HowItWorksPage.tsx`<br>`frontend/src/marketing/pages/PartnersPage.tsx`<br>`frontend/src/marketing/pages/PlanDetailPage.tsx`<br>`frontend/src/marketing/pages/PlansPage.tsx`<br>`frontend/src/marketing/pages/PrivacyPage.tsx`<br>`frontend/src/marketing/pages/TermsPage.tsx`<br>`frontend/src/provider/ProviderWorkspace.tsx`<br>`frontend/src/styles.css` |
| frontend/src/marketing/components/ChatPanel.tsx | A | GREETING_TEXT, SUGGESTED_QUESTIONS, ChatMessage, ChatPanel | `frontend/src/marketing/components/ChatPanel.css` |
| frontend/src/marketing/components/ChatbotLauncher.tsx | A | ChatbotLauncher | `frontend/src/marketing/components/ChatPanel.tsx`<br>`frontend/src/marketing/components/ChatbotLauncher.css` |
| frontend/src/marketing/components/MarketingFooter.tsx | A | SITE_LINKS, MarketingFooter | None |
| frontend/src/marketing/components/MarketingHeader.tsx | A | NAV_LINKS, MarketingHeader | None |
| frontend/src/marketing/components/MarketingLayout.tsx | A | MarketingLayout | `frontend/src/marketing/components/ChatbotLauncher.tsx`<br>`frontend/src/marketing/components/MarketingFooter.tsx`<br>`frontend/src/marketing/components/MarketingHeader.tsx`<br>`frontend/src/marketing/components/MarketingLayout.css`<br>`frontend/src/marketing/marketing.css`<br>`frontend/src/marketing/tokens.css` |
| frontend/src/marketing/components/PageShell.tsx | A | PageShell | None |
| frontend/src/marketing/components/Section.tsx | A | Section | None |
| frontend/src/marketing/components/SurfaceCard.tsx | A | SurfaceCard | None |
| frontend/src/marketing/components/index.ts | A | PageShell / Section / SurfaceCard barrel + theme CSS imports | `frontend/src/marketing/components/PageShell.tsx`<br>`frontend/src/marketing/components/Section.tsx`<br>`frontend/src/marketing/components/SurfaceCard.tsx`<br>`frontend/src/marketing/marketing.css`<br>`frontend/src/marketing/tokens.css` |
| frontend/src/marketing/hooks/useScrollReveal.ts | C | useScrollReveal | None |
| frontend/src/marketing/pages/AboutPage.tsx | A | AboutPage | `frontend/src/marketing/components/index.ts`<br>`frontend/src/marketing/pages/AboutPage.css` |
| frontend/src/marketing/pages/ClaimsExplainedPage.tsx | A | ClaimsExplainedPage | `frontend/src/marketing/components/index.ts`<br>`frontend/src/marketing/pages/ClaimsExplainedPage.css` |
| frontend/src/marketing/pages/ContactPage.tsx | A | ContactPage | `frontend/src/marketing/components/index.ts`<br>`frontend/src/marketing/pages/ContactPage.css` |
| frontend/src/marketing/pages/DisclaimerPage.tsx | A | DisclaimerPage | `frontend/src/marketing/components/index.ts`<br>`frontend/src/marketing/pages/LegalPages.css` |
| frontend/src/marketing/pages/FaqPage.tsx | A | FaqPage | `frontend/src/marketing/components/index.ts`<br>`frontend/src/marketing/pages/FaqPage.css` |
| frontend/src/marketing/pages/GuidePage.tsx | A | GuidePage | `frontend/src/marketing/components/index.ts`<br>`frontend/src/marketing/pages/GuidePage.css` |
| frontend/src/marketing/pages/GuideTopicPage.tsx | A | GuideTopicPage | `frontend/src/marketing/components/index.ts` |
| frontend/src/marketing/pages/HomePage.tsx | A | getPlanPositioning, HomePage | `frontend/src/api.ts`<br>`frontend/src/marketing/components/index.ts`<br>`frontend/src/marketing/pages/HomePage.css` |
| frontend/src/marketing/pages/HowItWorksPage.tsx | A | HowItWorksPage | `frontend/src/marketing/components/index.ts`<br>`frontend/src/marketing/pages/HowItWorksPage.css` |
| frontend/src/marketing/pages/PartnersPage.tsx | A | Provider, TIER_LABELS, PartnersPage | `frontend/src/api.ts`<br>`frontend/src/marketing/components/index.ts`<br>`frontend/src/marketing/pages/PartnersPage.css` |
| frontend/src/marketing/pages/PlanDetailPage.tsx | A | getPlanPersona, PlanDetailPage | `frontend/src/api.ts`<br>`frontend/src/marketing/components/index.ts`<br>`frontend/src/marketing/pages/PlanDetailPage.css` |
| frontend/src/marketing/pages/PlansPage.tsx | A | coverageLabel, PlansPage | `frontend/src/api.ts`<br>`frontend/src/marketing/components/index.ts`<br>`frontend/src/marketing/pages/PlansPage.css` |
| frontend/src/marketing/pages/PrivacyPage.tsx | A | PrivacyPage | `frontend/src/marketing/components/index.ts`<br>`frontend/src/marketing/pages/LegalPages.css` |
| frontend/src/marketing/pages/TermsPage.tsx | A | TermsPage | `frontend/src/marketing/components/index.ts`<br>`frontend/src/marketing/pages/LegalPages.css` |
| frontend/src/provider/ProviderApplications.tsx | B | ProviderApplications | `frontend/src/api.ts`<br>`frontend/src/provider/types.ts` |
| frontend/src/provider/ProviderFinancialAccounts.tsx | B | ProviderFinancialAccounts | `frontend/src/api.ts` |
| frontend/src/provider/ProviderFlagForm.tsx | B | ProviderFlagForm | `frontend/src/api.ts` |
| frontend/src/provider/ProviderPolicies.tsx | B | ProviderPolicies | `frontend/src/Feedback.tsx`<br>`frontend/src/api.ts`<br>`frontend/src/provider/types.ts` |
| frontend/src/provider/ProviderQuoteForm.tsx | B | ProviderQuoteForm | `frontend/src/api.ts` |
| frontend/src/provider/ProviderWorkspace.tsx | B | ProviderWorkspace | `frontend/src/api.ts`<br>`frontend/src/provider/ProviderApplications.tsx`<br>`frontend/src/provider/ProviderFinancialAccounts.tsx`<br>`frontend/src/provider/ProviderFlagForm.tsx`<br>`frontend/src/provider/ProviderPolicies.tsx`<br>`frontend/src/provider/ProviderQuoteForm.tsx` |
| frontend/src/provider/types.ts | B | ProviderApplication, ProviderQuotation, ProviderPolicy | None |
| frontend/src/vite-env.d.ts | D | Vite ambient type declarations | None |

Local functions and nested helpers move with their owning file; no function bodies are cut out in Phase 1. Every co-located CSS file and all other repository files are classified in the inventory below.

## Complete frontend-to-backend call map

Every literal /api path in frontend source is listed below and matched against backend decorators by path shape. Dynamic frontend template variables are equivalent to backend `{parameter}` segments; query strings do not change route matching. HTTP methods shown are registered backend methods, verified by syntax-only AST parsing. Matching does not execute handlers. `api.ts` supplies auth/idempotency/error handling; keep that contract unchanged. Indirect calls through child components are covered by the import inventory and route descriptions above.

| Frontend caller | Bucket | Literal path/template | Registered method(s) | Existing backend registration |
| --- | --- | --- | --- | --- |
| frontend/src/Broker.tsx | B | /api/broker/appeals | GET | `GET /api/broker/appeals (backend/app/main.py:1216)` |
| frontend/src/Broker.tsx | B | /api/broker/appeals/${item.id}/review | POST | `POST /api/broker/appeals/{appeal_id}/review (backend/app/main.py:1243)` |
| frontend/src/Broker.tsx | B | /api/broker/cases/${selectedApplicant} | GET | `GET /api/broker/cases/{applicant_id} (backend/app/main.py:771)` |
| frontend/src/Broker.tsx | B | /api/broker/reassessments | GET | `GET /api/broker/reassessments (backend/app/main.py:1045)` |
| frontend/src/Broker.tsx | B | /api/broker/reassessments/${item.id}/review | POST | `POST /api/broker/reassessments/{reassessment_id}/review (backend/app/main.py:1067)` |
| frontend/src/Broker.tsx | B | /api/broker/recommendations | GET | `GET /api/broker/recommendations (backend/app/main.py:703)` |
| frontend/src/Broker.tsx | B | /api/broker/recommendations/${item.id}/review | POST | `POST /api/broker/recommendations/{recommendation_id}/review (backend/app/main.py:795)` |
| frontend/src/Broker.tsx | B | /api/broker/worklist | GET | `GET /api/broker/worklist (backend/app/main.py:727)` |
| frontend/src/ClaimAdvocate.tsx | A | /api/policies/${policyId}/claim-intakes/advocate | POST | `POST /api/policies/{policy_id}/claim-intakes/advocate (backend/app/claim_agent.py:754)` |
| frontend/src/Conversation.tsx | A | /api/cases/${caseId} | GET | `GET /api/cases/{case_id} (backend/app/main.py:377)` |
| frontend/src/Conversation.tsx | A | /api/cases/${caseId}/messages | POST | `POST /api/cases/{case_id}/messages (backend/app/main.py:401)` |
| frontend/src/Conversation.tsx | A | /api/marketplace/cases/${caseId}/consent | POST | `POST /api/marketplace/cases/{case_id}/consent (backend/app/marketplace_matching.py:148)` |
| frontend/src/Conversation.tsx | A | /api/marketplace/cases/${caseId}/recommendations | GET | `GET /api/marketplace/cases/{case_id}/recommendations (backend/app/marketplace_matching.py:134)` |
| frontend/src/Conversation.tsx | A | /api/me/profile | GET, PATCH | `GET /api/me/profile (backend/app/main.py:321)`<br>`PATCH /api/me/profile (backend/app/main.py:335)` |
| frontend/src/MarketplaceBrokerPanel.tsx | B | /api/broker/marketplace/applications | GET | `GET /api/broker/marketplace/applications (backend/app/marketplace_broker.py:221)` |
| frontend/src/MarketplaceBrokerPanel.tsx | B | /api/broker/marketplace/applications/${selected} | GET | `GET /api/broker/marketplace/applications/{application_id} (backend/app/marketplace_broker.py:246)` |
| frontend/src/MarketplaceBrokerPanel.tsx | B | /api/broker/marketplace/applications/${selected}/checkpoint-2 | POST | `POST /api/broker/marketplace/applications/{application_id}/checkpoint-2 (backend/app/marketplace_broker.py:339)` |
| frontend/src/MarketplaceBrokerPanel.tsx | B | /api/broker/marketplace/provider-performance | GET | `GET /api/broker/marketplace/provider-performance (backend/app/marketplace_broker.py:174)` |
| frontend/src/MarketplaceJourney.tsx | A | /api/marketplace/cases/${caseId}/consent | POST | `POST /api/marketplace/cases/{case_id}/consent (backend/app/marketplace_matching.py:148)` |
| frontend/src/MarketplaceJourney.tsx | A | /api/marketplace/cases/${caseId}/quotations | GET | `GET /api/marketplace/cases/{case_id}/quotations (backend/app/marketplace_selection.py:223)` |
| frontend/src/MarketplaceJourney.tsx | A | /api/marketplace/cases/${caseId}/recommendations | GET | `GET /api/marketplace/cases/{case_id}/recommendations (backend/app/marketplace_matching.py:134)` |
| frontend/src/MarketplaceJourney.tsx | A | /api/marketplace/quotations/${choice.quotation_id}/select | POST | `POST /api/marketplace/quotations/{quotation_id}/select (backend/app/marketplace_selection.py:230)` |
| frontend/src/ProfileEditor.tsx | A | /api/documents | POST | `POST /api/documents (backend/app/main.py:534)` |
| frontend/src/ProfileEditor.tsx | A | /api/extractions/${extraction.id}/accept | POST | `POST /api/extractions/{document_id}/accept (backend/app/main.py:547)` |
| frontend/src/ProfileEditor.tsx | A | /api/me/profile | GET, PATCH | `GET /api/me/profile (backend/app/main.py:321)`<br>`PATCH /api/me/profile (backend/app/main.py:335)` |
| frontend/src/Providers.tsx | A | /api/providers?plan_id=${encodeURIComponent(planId)}&emirate=${encodeURIComponent(emirate)} | GET | `GET /api/providers (backend/app/main.py:1492)` |
| frontend/src/Shopping.tsx | A | /api/applications/${applicationId} | GET | `GET /api/applications/{application_id} (backend/app/main.py:688)` |
| frontend/src/Shopping.tsx | A | /api/applications/${applicationId}/submit | POST | `POST /api/applications/{application_id}/submit (backend/app/main.py:860)` |
| frontend/src/Shopping.tsx | A | /api/applications/prepare | POST | `POST /api/applications/prepare (backend/app/main.py:624)` |
| frontend/src/Shopping.tsx | A | /api/cases | GET, POST | `GET /api/cases (backend/app/main.py:347)`<br>`POST /api/cases (backend/app/main.py:353)` |
| frontend/src/Shopping.tsx | A | /api/instalments/${id}/payment-order | POST | `POST /api/instalments/{installment_id}/payment-order (backend/app/main.py:1369)` |
| frontend/src/Shopping.tsx | A | /api/marketplace/applications | GET | `GET /api/marketplace/applications (backend/app/marketplace_selection.py:163)` |
| frontend/src/Shopping.tsx | A | /api/marketplace/notifications | GET | `GET /api/marketplace/notifications (backend/app/marketplace_selection.py:183)` |
| frontend/src/Shopping.tsx | A | /api/marketplace/policies | GET | `GET /api/marketplace/policies (backend/app/marketplace_selection.py:279)` |
| frontend/src/Shopping.tsx | A | /api/me/profile | GET, PATCH | `GET /api/me/profile (backend/app/main.py:321)`<br>`PATCH /api/me/profile (backend/app/main.py:335)` |
| frontend/src/Shopping.tsx | A | /api/payment-orders/${order.id}/simulate | POST | `POST /api/payment-orders/{order_id}/simulate (backend/app/main.py:1424)` |
| frontend/src/Shopping.tsx | A | /api/payments/verify | POST | `POST /api/payments/verify (backend/app/main.py:1450)` |
| frontend/src/Shopping.tsx | A | /api/policies | GET | `GET /api/policies (backend/app/main.py:920)` |
| frontend/src/Shopping.tsx | A | /api/policies/${policyId} | GET | `GET /api/policies/{policy_id} (backend/app/main.py:935)` |
| frontend/src/Shopping.tsx | A | /api/policies/${policyId}/appeals | POST | `POST /api/policies/{policy_id}/appeals (backend/app/main.py:1157)` |
| frontend/src/Shopping.tsx | A | /api/policies/${policyId}/claim-intakes | GET | `GET /api/policies/{policy_id}/claim-intakes (backend/app/claim_agent.py:946)` |
| frontend/src/Shopping.tsx | A | /api/policies/${policyId}/claim-intakes/${intakeId}/attachments | POST | `POST /api/policies/{policy_id}/claim-intakes/{claim_intake_id}/attachments (backend/app/claim_agent.py:680)` |
| frontend/src/Shopping.tsx | A | /api/policies/${policyId}/claim-intakes/${item.id}/appeal | POST | `POST /api/policies/{policy_id}/claim-intakes/{claim_intake_id}/appeal (backend/app/claim_agent.py:1463)` |
| frontend/src/Shopping.tsx | A | /api/policies/${policyId}/claim-intakes/${item.id}/appeal-draft | POST | `POST /api/policies/{policy_id}/claim-intakes/{claim_intake_id}/appeal-draft (backend/app/claim_agent.py:1448)` |
| frontend/src/Shopping.tsx | A | /api/policies/${policyId}/claim-intakes/${item.id}/attachments | POST | `POST /api/policies/{policy_id}/claim-intakes/{claim_intake_id}/attachments (backend/app/claim_agent.py:680)` |
| frontend/src/Shopping.tsx | A | /api/policies/${policyId}/claim-intakes/${item.id}/provisional-letter | GET | `GET /api/policies/{policy_id}/claim-intakes/{claim_intake_id}/provisional-letter (backend/app/claim_agent.py:1423)` |
| frontend/src/Shopping.tsx | A | /api/policies/${policyId}/claim-intakes/appeal-draft | POST | `POST /api/policies/{policy_id}/claim-intakes/appeal-draft (backend/app/claim_agent.py:1070)` |
| frontend/src/Shopping.tsx | A | /api/policies/${policyId}/claim-intakes/free-form | POST | `POST /api/policies/{policy_id}/claim-intakes/free-form (backend/app/claim_agent.py:618)` |
| frontend/src/Shopping.tsx | A | /api/policies/${policyId}/claim-intakes/structured | POST | `POST /api/policies/{policy_id}/claim-intakes/structured (backend/app/claim_agent.py:595)` |
| frontend/src/Shopping.tsx | A | /api/policies/${policyId}/reassess | POST | `POST /api/policies/{policy_id}/reassess (backend/app/main.py:1003)` |
| frontend/src/Shopping.tsx | A | /api/policies/${policyId}/updates | GET | `GET /api/policies/{policy_id}/updates (backend/app/main.py:1483)` |
| frontend/src/Shopping.tsx | A | /api/policies/import | POST | `POST /api/policies/import (backend/app/main.py:1344)` |
| frontend/src/Shopping.tsx | A | /api/quotes/${quoteId} | GET | `GET /api/quotes/{quote_id} (backend/app/main.py:602)` |
| frontend/src/Shopping.tsx | A | /api/sources | GET | `GET /api/sources (backend/app/main.py:195)` |
| frontend/src/Voice.tsx | A | /api/voice/transcriptions | POST | `POST /api/voice/transcriptions (backend/app/main.py:484)` |
| frontend/src/api.ts | D | /api/quotes/${id}/download | GET | `GET /api/quotes/{quote_id}/download (backend/app/main.py:614)` |
| frontend/src/broker/ClaimOperations.tsx | B | /api/broker/claims/${claimId.trim()}/replay | GET | `GET /api/broker/claims/{claim_intake_id}/replay (backend/app/claim_agent.py:1619)` |
| frontend/src/broker/ClaimOperations.tsx | B | /api/broker/claims/observability | GET | `GET /api/broker/claims/observability (backend/app/claim_agent.py:1561)` |
| frontend/src/broker/ClaimOperations.tsx | B | /api/broker/claims/quality-samples | GET | `GET /api/broker/claims/quality-samples (backend/app/claim_agent.py:1595)` |
| frontend/src/broker/ClaimOperations.tsx | B | /api/broker/claims/quality-samples/${id}/review | POST | `POST /api/broker/claims/quality-samples/{sample_id}/review (backend/app/claim_agent.py:1604)` |
| frontend/src/broker/ClaimOperations.tsx | B | /api/broker/claims/rules | GET | `GET /api/broker/claims/rules (backend/app/claim_agent.py:1524)` |
| frontend/src/broker/ClaimOperations.tsx | B | /api/broker/claims/rules/${kind} | POST | `POST /api/broker/claims/rules/{rule_kind} (backend/app/claim_agent.py:1534)` |
| frontend/src/broker/ClaimReview.tsx | B | /api/broker/claims | GET | `GET /api/broker/claims (backend/app/claim_agent.py:1232)` |
| frontend/src/broker/ClaimReview.tsx | B | /api/broker/claims/${claim.id}/appeal-review | POST | `POST /api/broker/claims/{appeal_id}/appeal-review (backend/app/claim_agent.py:1496)` |
| frontend/src/broker/ClaimReview.tsx | B | /api/broker/claims/${claim.id}/review | POST | `POST /api/broker/claims/{claim_intake_id}/review (backend/app/claim_agent.py:1308)` |
| frontend/src/broker/ClaimReview.tsx | B | /api/broker/claims/${claimId}/documents/${documentId}/original | GET | `GET /api/broker/claims/{claim_intake_id}/documents/{document_id}/original (backend/app/claim_agent.py:1257)` |
| frontend/src/broker/ClaimReview.tsx | B | /api/broker/claims/analytics | GET | `GET /api/broker/claims/analytics (backend/app/claim_agent.py:1278)` |
| frontend/src/broker/ClaimReview.tsx | B | /api/broker/claims/on-call-shifts | POST | `POST /api/broker/claims/on-call-shifts (backend/app/claim_agent.py:1219)` |
| frontend/src/main.tsx | D | /api/config | GET | `GET /api/config (backend/app/main.py:176)` |
| frontend/src/main.tsx | D | /api/marketplace/notifications | GET | `GET /api/marketplace/notifications (backend/app/marketplace_selection.py:183)` |
| frontend/src/main.tsx | D | /api/me/access | GET | `GET /api/me/access (backend/app/main.py:316)` |
| frontend/src/main.tsx | D | /api/policies | GET | `GET /api/policies (backend/app/main.py:920)` |
| frontend/src/marketing/components/ChatPanel.tsx | A | /api/public/assistant/messages | POST | `POST /api/public/assistant/messages (backend/app/main.py:226)` |
| frontend/src/marketing/pages/HomePage.tsx | A | /api/public/marketplace-partners | GET | `GET /api/public/marketplace-partners (backend/app/main.py:292)` |
| frontend/src/marketing/pages/HomePage.tsx | A | /api/public/marketplace-plans | GET | `GET /api/public/marketplace-plans (backend/app/main.py:275)` |
| frontend/src/marketing/pages/PartnersPage.tsx | A | /api/public/marketplace-partners | GET | `GET /api/public/marketplace-partners (backend/app/main.py:292)` |
| frontend/src/marketing/pages/PlanDetailPage.tsx | A | /api/public/marketplace-plans | GET | `GET /api/public/marketplace-plans (backend/app/main.py:275)` |
| frontend/src/marketing/pages/PlansPage.tsx | A | /api/public/marketplace-plans | GET | `GET /api/public/marketplace-plans (backend/app/main.py:275)` |
| frontend/src/provider/ProviderApplications.tsx | B | /api/provider/applications | GET | `GET /api/provider/applications (backend/app/provider_console.py:150)` |
| frontend/src/provider/ProviderFinancialAccounts.tsx | B | /api/provider/policies/${policyId}/payments | GET | `GET /api/provider/policies/{policy_id}/payments (backend/app/provider_console.py:320)` |
| frontend/src/provider/ProviderFlagForm.tsx | B | /api/provider/policies/${policyId}/flags | POST | `POST /api/provider/policies/{policy_id}/flags (backend/app/provider_console.py:343)` |
| frontend/src/provider/ProviderPolicies.tsx | B | /api/provider/policies | GET | `GET /api/provider/policies (backend/app/provider_console.py:287)` |
| frontend/src/provider/ProviderPolicies.tsx | B | /api/provider/policies/${policy.id}/discontinue | POST | `POST /api/provider/policies/{policy_id}/discontinue (backend/app/provider_console.py:299)` |
| frontend/src/provider/ProviderPolicies.tsx | B | /api/provider/policies/${quote.id}/start | POST | `POST /api/provider/policies/{quotation_id}/start (backend/app/provider_console.py:228)` |
| frontend/src/provider/ProviderPolicies.tsx | B | /api/provider/quotations | GET | `GET /api/provider/quotations (backend/app/provider_console.py:199)` |
| frontend/src/provider/ProviderPolicies.tsx | B | /api/provider/quotations/${quote.id}/accept | POST | `POST /api/provider/quotations/{quotation_id}/accept (backend/app/provider_console.py:212)` |
| frontend/src/provider/ProviderQuoteForm.tsx | B | /api/provider/applications/${applicationId}/assistant | POST | `POST /api/provider/applications/{application_id}/assistant (backend/app/provider_console.py:364)` |
| frontend/src/provider/ProviderQuoteForm.tsx | B | /api/provider/applications/${applicationId}/quote | POST | `POST /api/provider/applications/{application_id}/quote (backend/app/provider_console.py:165)` |
| frontend/src/provider/ProviderWorkspace.tsx | B | /api/me/access | GET | `GET /api/me/access (backend/app/main.py:316)` |

Additional non-Helm calls: Supabase Auth via configureAuth in api.ts and Login; browser speech synthesis in Voice.tsx; optional Razorpay checkout script in Shopping.tsx. Download URLs/Blob object URLs are client-side or already represented above. These integrations stay on the customer site. Providers.tsx is a customer hospital/network map using `/api/providers`; it is unrelated to the professional ProviderWorkspace.

## Every baseline file, exactly one bucket

This table is a PROPOSED classification, not a move manifest. After approval, MANIFEST.md will record actual MOVE/COPY/ORIGINAL-SNAPSHOT operations with exact paths and hashes. All B/C targets preserve the original full path inside their group.

| Baseline path | Bucket | Group / ownership | Proposed handling |
| --- | --- | --- | --- |
| .github/workflows/checks.yml | D | shared | Keep shared tooling/docs; archive whole original before any future edit |
| .gitignore | D | shared | Keep shared tooling/docs; archive whole original before any future edit |
| README.md | D | shared | Keep shared tooling/docs; archive whole original before any future edit |
| backend/.env.example | D | shared | Protected shared backend; leave unchanged |
| backend/app/__init__.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/agents.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/auth.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/claim_agent.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/claims_lifecycle.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/claims_phase_one.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/config.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/contracts.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/db.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/documents.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/domain.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/explanations.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/fixture_tour.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/main.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/marketplace_broker.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/marketplace_matching.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/marketplace_models.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/marketplace_selection.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/models.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/payments.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/provider_console.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/public_assistant.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/services.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/servicing.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/sources.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/voice.py | D | shared | Protected shared backend; leave unchanged |
| backend/app/worker.py | D | shared | Protected shared backend; leave unchanged |
| backend/data/hackathon_data.json | D | shared | Protected shared backend; leave unchanged |
| backend/data/source_registry.json | D | shared | Protected shared backend; leave unchanged |
| backend/helm_api.egg-info/PKG-INFO | D | shared | Protected shared backend; leave unchanged |
| backend/helm_api.egg-info/SOURCES.txt | D | shared | Protected shared backend; leave unchanged |
| backend/helm_api.egg-info/dependency_links.txt | D | shared | Protected shared backend; leave unchanged |
| backend/helm_api.egg-info/requires.txt | D | shared | Protected shared backend; leave unchanged |
| backend/helm_api.egg-info/top_level.txt | D | shared | Protected shared backend; leave unchanged |
| backend/pyproject.toml | D | shared | Protected shared backend; leave unchanged |
| backend/scripts/bootstrap_demo_accounts.py | D | shared | Protected shared backend; leave unchanged |
| backend/scripts/configure_local.py | D | shared | Protected shared backend; leave unchanged |
| backend/scripts/export_fixture_tour.py | D | shared | Protected shared backend; leave unchanged |
| backend/scripts/fixture_tour.py | D | shared | Protected shared backend; leave unchanged |
| backend/scripts/generate_migration.py | D | shared | Protected shared backend; leave unchanged |
| backend/scripts/live_smoke.py | D | shared | Protected shared backend; leave unchanged |
| backend/scripts/refresh_sources.py | D | shared | Protected shared backend; leave unchanged |
| backend/scripts/seed_marketplace_providers.py | D | shared | Protected shared backend; leave unchanged |
| backend/scripts/verify_db_replay.py | D | shared | Protected shared backend; leave unchanged |
| backend/scripts/verify_replay.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/conftest.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_agentic_claims_phase_one.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_agentic_claims_phases_two_three.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_broker_assignment.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_broker_auth.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_claim_agent.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_claim_management_completion.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_claim_originals.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_claim_review.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_claim_staging.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_document_limits.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_explanations.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_fixture_profiles.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_fixture_tour.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_intake_state_machine.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_marketplace_checkpoints.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_marketplace_full_journey.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_marketplace_matching.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_marketplace_modern_features.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_marketplace_seed.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_marketplace_selection.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_phase_one.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_provider_console.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_public_assistant.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_regular_profile_reset.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_servicing_api.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_servicing_domain.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_sources.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_voice.py | D | shared | Protected shared backend; leave unchanged |
| backend/tests/test_worker.py | D | shared | Protected shared backend; leave unchanged |
| backend/uv.lock | D | shared | Protected shared backend; leave unchanged |
| docs/deliverable/fixture_tour_report.json | E | needs-decision | Leave in place; needs decision |
| docs/fixture_tour_latest.json | E | needs-decision | Leave in place; needs decision |
| frontend/.env.example | D | shared | Protected environment template; no Phase 1 read/copy/edit |
| frontend/index.html | A | main-site | Keep customer/public behavior |
| frontend/package-lock.json | D | shared | Keep shared tooling/docs; archive whole original before any future edit |
| frontend/package.json | D | shared | Keep shared tooling/docs; archive whole original before any future edit |
| frontend/public/assets/helm-assistant.json | C | _unused | Proposed git mv to archive/_unused/frontend/public/assets/helm-assistant.json |
| frontend/public/assets/robot.json | A | main-site | Keep customer/public behavior |
| frontend/src/Broker.tsx | B | broker-workspace | Proposed git mv to archive/broker-workspace/frontend/src/Broker.tsx |
| frontend/src/CalculationStepper.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/ClaimAdvocate.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/Conversation.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/CoverageSummary.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/Feedback.tsx | D | shared | Keep; whole original snapshot required before any future edit; copy dashboard-needed helpers/styles |
| frontend/src/FormActions.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/MarketplaceBrokerPanel.tsx | B | broker-workspace | Proposed git mv to archive/broker-workspace/frontend/src/MarketplaceBrokerPanel.tsx |
| frontend/src/MarketplaceJourney.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/PolicyNotifications.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/ProfileEditor.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/Providers.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/Shopping.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/Voice.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/api.ts | D | shared | Keep; whole original snapshot required before any future edit; copy dashboard-needed helpers/styles |
| frontend/src/broker/ClaimOperations.tsx | B | claim-review | Proposed git mv to archive/claim-review/frontend/src/broker/ClaimOperations.tsx |
| frontend/src/broker/ClaimReview.tsx | B | claim-review | Proposed git mv to archive/claim-review/frontend/src/broker/ClaimReview.tsx |
| frontend/src/components/CalculationStepper.tsx | C | _unused | Proposed git mv to archive/_unused/frontend/src/components/CalculationStepper.tsx |
| frontend/src/foundation.css | D | shared | Keep; whole original snapshot required before any future edit; copy dashboard-needed helpers/styles |
| frontend/src/main.tsx | D | shared | Keep; whole original snapshot required before any future edit; copy dashboard-needed helpers/styles |
| frontend/src/marketing/components/ChatPanel.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/components/ChatPanel.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/components/ChatbotLauncher.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/components/ChatbotLauncher.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/components/MarketingFooter.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/components/MarketingHeader.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/components/MarketingLayout.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/components/MarketingLayout.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/components/PageShell.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/components/Section.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/components/SurfaceCard.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/components/index.ts | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/hooks/useScrollReveal.ts | C | _unused | Proposed git mv to archive/_unused/frontend/src/marketing/hooks/useScrollReveal.ts |
| frontend/src/marketing/marketing.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/AboutPage.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/AboutPage.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/ClaimsExplainedPage.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/ClaimsExplainedPage.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/ContactPage.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/ContactPage.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/DisclaimerPage.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/FaqPage.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/FaqPage.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/GuidePage.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/GuidePage.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/GuideTopicPage.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/HomePage.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/HomePage.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/HowItWorksPage.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/HowItWorksPage.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/LegalPages.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/PartnersPage.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/PartnersPage.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/PlanDetailPage.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/PlanDetailPage.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/PlansPage.css | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/PlansPage.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/PrivacyPage.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/pages/TermsPage.tsx | A | main-site | Keep customer/public behavior |
| frontend/src/marketing/tokens.css | A | main-site | Keep customer/public behavior |
| frontend/src/provider/ProviderApplications.tsx | B | provider-workspace | Proposed git mv to archive/provider-workspace/frontend/src/provider/ProviderApplications.tsx |
| frontend/src/provider/ProviderFinancialAccounts.tsx | B | provider-workspace | Proposed git mv to archive/provider-workspace/frontend/src/provider/ProviderFinancialAccounts.tsx |
| frontend/src/provider/ProviderFlagForm.tsx | B | provider-workspace | Proposed git mv to archive/provider-workspace/frontend/src/provider/ProviderFlagForm.tsx |
| frontend/src/provider/ProviderPolicies.tsx | B | provider-workspace | Proposed git mv to archive/provider-workspace/frontend/src/provider/ProviderPolicies.tsx |
| frontend/src/provider/ProviderQuoteForm.tsx | B | provider-workspace | Proposed git mv to archive/provider-workspace/frontend/src/provider/ProviderQuoteForm.tsx |
| frontend/src/provider/ProviderWorkspace.tsx | B | provider-workspace | Proposed git mv to archive/provider-workspace/frontend/src/provider/ProviderWorkspace.tsx |
| frontend/src/provider/types.ts | B | provider-workspace | Proposed git mv to archive/provider-workspace/frontend/src/provider/types.ts |
| frontend/src/styles.css | D | shared | Keep; whole original snapshot required before any future edit; copy dashboard-needed helpers/styles |
| frontend/src/vite-env.d.ts | D | shared | Keep; whole original snapshot required before any future edit; copy dashboard-needed helpers/styles |
| frontend/tsconfig.json | D | shared | Keep shared tooling/docs; archive whole original before any future edit |
| frontend/vite.config.ts | D | shared | Keep shared tooling/docs; archive whole original before any future edit |
| package-lock.json | D | shared | Keep shared tooling/docs; archive whole original before any future edit |
| package.json | D | shared | Keep shared tooling/docs; archive whole original before any future edit |
| playwright.config.ts | D | shared | Keep shared tooling/docs; archive whole original before any future edit |
| scripts/start-prototype.ps1 | E | needs-decision | Leave in place; needs decision |
| supabase/.gitignore | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/config.toml | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/migrations/202609120001_phase_one.sql | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/migrations/202609120002_sources.sql | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/migrations/202609130001_servicing.sql | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/migrations/202609130002_policy_reassessments.sql | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/migrations/202609130003_reassessment_review.sql | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/migrations/202609130004_broker_assignments.sql | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/migrations/202609190002_marketplace_pivot.sql | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/migrations/202609190003_marketplace_checkpoints.sql | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/migrations/202609200001_claim_staging.sql | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/migrations/202609220001_member_led_marketplace.sql | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/migrations/202609230001_agentic_claims_phase_one.sql | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/migrations/202609230002_agentic_claims_phases_two_three.sql | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/migrations/202609240001_claim_document_files.sql | D | shared | Protected database/config/migrations; leave unchanged |
| supabase/migrations/202610200001_restore_policy_binding_checkpoint.sql | D | shared | Protected database/config/migrations; leave unchanged |
| tests/e2e/broker-marketplace.spec.ts | B | broker-workspace | Proposed git mv to archive/broker-workspace/tests/e2e/broker-marketplace.spec.ts |
| tests/e2e/claim-message.spec.ts | A | main-site | Keep customer/public behavior |
| tests/e2e/claim-review.spec.ts | B | claim-review | Proposed git mv to archive/claim-review/tests/e2e/claim-review.spec.ts |
| tests/e2e/landing.spec.ts | A | main-site | Keep customer/public behavior |
| tests/e2e/marketplace-selection.spec.ts | A | main-site | Keep customer/public behavior |
| tests/e2e/provider-workspace.spec.ts | B | provider-workspace | Proposed git mv to archive/provider-workspace/tests/e2e/provider-workspace.spec.ts |
| tests/e2e/support.ts | D | shared | Keep; copy into each archived dashboard test suite |
| tests/e2e/ui-resilience.spec.ts | A | main-site | Keep customer/public behavior |

## Planned preservation and verification after approval

1. Create archive README.md, MANIFEST.md, DEPENDENCIES.md and one README per actual group. Record MOVE, COPY and ORIGINAL-SNAPSHOT separately; include exact source/destination paths, reason, group and baseline content hash. Never copy real environment files or secrets.
2. Use git mv for approved B/C files and commit one group at a time: `archive: move <group> out of main site (no deletions)`. Keep shared originals in the main tree. Copy each mixed original whole into archive/_original_copies/<original-path> before editing its kept version; the safety tag alone does not replace that required copy.
3. Generate archive/restore.sh with the exact inverse git mv for every actual move; do not execute it. Document how to restore mixed edited files from their original copies without overwriting newer work blindly. No restore operation occurs in Phase 1.
4. Preserve package manifests/dependencies and API calls. Repair only routing, navigation, frontend role guidance and necessary import/build/test boundaries, after originals are archived. Do not change backend, Supabase, migrations, auth helpers or API contracts.
5. Run npm run build and frontend tsc --noEmit; run the existing Playwright customer suite and any configured lint/check commands. There is no configured ESLint or Vitest suite. Start the frontend dev server and inspect all kept routes and navigation. Record failures/limitations; do not hide them through broad excludes.
6. Compare the safety-tag file list against original paths plus manifest-mapped archive paths. Validate moved/copied blobs by hash and byte-compare originals for every edited file. Required final missing-baseline-file count: zero. Confirm protected paths and API/auth files have zero diff. Verify restore.sh exists and was not run.

## Phase 1 verification and approval boundary

- Upstream revision and pristine checkout verified before creating safety tag/branch.
- All 187 baseline paths still exist; no moves or application-code edits have occurred.
- Classification count: A=56, B=14, C=3, D=111, E=3; total=187.
- 89 literal frontend API-path uses matched existing backend route registrations; no missing literal endpoint found.
- Backend routes were read as source only. Database, migrations, real environment files, credentials and backend API contracts were not changed or executed.
- Builds, runtime UI checks, final restoration script and post-move no-loss audit are pending approval and later phases. This audit is not a claim that the restructuring is complete.
- STOP: await explicit approval of this classification. If no approval arrives, do not enter Phase 2. E items stay where they are unless separately decided.
