# Helm AI quotation workflow — current prototype

Updated25 October2026. Shared source: https://github.com/GarvGupta25/Helm_AI. Use `U:\projects\Helm_AI`; `Insurance_UAE` is another checkout. Development author: **Utkarsh Raj**. Original implementation history is retained in Git and phase reports; this document describes the current journey.

## Run and collaborate

1. Inspect `git status`, fetch origin and `git pull --ff-only` on a clean tree. Preserve a collaborator's local edits. Use the existing branch or a `codex/` branch for independent work; never force-push shared history.
2. `uv sync --project backend`; start `npm run api:prototype`. This explicitly uses `.runtime/uk-e2e.db`, an isolated encryption key and a separate chatbot-feedback database, configured real verification and no live Groq calls. It creates current demo tables and seeds fictional catalogues/accounts. Never substitute the user's configured database.
3. After health at `http://127.0.0.1:8000/health` is ready, start `npm run worker:prototype`. The worker processes synthetic quotations, private notifications, due broker follow-ups and retention every2s. It defaults to console; allow-listed provider testing requires explicit `--allow-configured-sandbox`.
4. For the new guided preview, set `$env:VITE_QUOTE_WIZARD='true'`, run `npm --prefix frontend run build`, then `npm --prefix frontend run preview`. Open `http://127.0.0.1:4174/get-cover/quote`. Vite dev works with the same flag. Start helpers hidden on Windows. Restart only the task's verified PIDs when needed. Stop API/worker before updating loaded Python binary packages on Windows.
5. Test the intended change, review the diff, commit with the agreed author, fetch/integrate new remote changes, then push. Per-phase results are in `docs/ux/WIZARD_PROGRESS.md`.

Default `VITE_QUOTE_WIZARD=false` keeps the original intake. `/get-cover/legacy-intake` always exposes it; `/get-cover/legacy-demo` keeps the older research comparison. Do not delete the fallback or remove the production guard without explicit owner approval.

## Visitor journey

- `/get-cover/quote`: choose manual or guided chat; both use the same canonical `JourneyProfile`, private `X-Journey-Session` capability and encrypted server draft. Never place this capability in a URL, log or screenshot.
- Per-topic routes: consent, people, region, start-date, budget, excess, hospitals, benefits/hospital, benefits/wellbeing, benefits/everyday. Autosave changes the draft; explicit confirmation creates a version and enables deterministic recommendations. The server validates seven essentials. Empty essential-benefit array is a reviewed choice; null is unanswered.
- `ready` checkpoint: show plans immediately or add optional existing-cover, underwriting, outpatient, postcode and fictional existing-condition answers. Show-plans stays available. Skipping means unanswered. `review` supports per-topic edit/return, confirmed history and Undo.
- `/get-cover/plans`: up to10 eligible variants, preserving original diverse top3. Sidebar filters are view-only; saving them requires explicit confirmation and a new profile version. Hard requirements never relax automatically. Select1–3 plans, inspect `/get-cover/plans/:planId`, or `/get-cover/compare`.
- `/get-cover/selection`: exact shared profile/selected plans; named insurer consent required, broker consent optional and initially unticked. This creates a reviewed receipt only. No account, policy or payment is created.
- `/get-cover/verify` and `/verify/code`: international calling-code entry or email fallback, separate verification permission, six-digit code. The isolated prototype uses a private local demo inbox and proves no real ownership. See `docs/ux/VERIFICATION_SETUP.md` for official allow-listed WhatsApp/SMTP configuration and external approval prerequisites.
- `/get-cover/access`:24/48-hour hashed, revocable link and idempotent synthetic requests. The existing worker makes one request per insurer containing all selected plan snapshots; per-plan statuses are exposed separately. Delivery remains private/local unless an operator explicitly enables a reviewed sandbox.
- `/my-quotes#<secret>` (legacy `/quote-dashboard#<secret>`): fragment token never enters the HTTP request/access log. An interstitial removes it from the address bar and waits for deliberate exchange. Single-use link creates an HttpOnly SameSite=Strict dashboard cookie lasting at most2h and never beyond the parent expiry. Reverification of the original contact is required to renew; old grants are revoked.
- `/my-quotes`: Quotations, Compare, Ask Helm, Documents, My answers, Broker. Received facts, explanations and PDFs remain synthetic. Explain/Compare/Recommend use stored facts and deterministic ranking; unsupported questions refuse. Optional configured Groq narration may only rearrange approved sentences with per-message consent. Answers cannot invent prices/eligibility.

## Broker and human review

Floating broker contact is available across journey pages. Preferred channel/time/note and current shortlist are shared only after explicit permission; withdrawal ends broker access. An early incomplete profile can request help. Cases remain unassigned unless configured/assigned by an administrator.

`/broker.html` is a separate authenticated entry. Supabase role and current assignment/consent are checked server-side. No real broker login is fabricated. Queue filters and assistant priorities use the earliest case/link/quotation deadline. The assistant assembles source-linked facts, missing/conflicting checklist prompts, needs summaries, rationale, comparison, underwriting/application draft packs and customer/follow-up messages. The JSON checklist is prototype wording pending legal review.

Drafts never send or export autonomously. A human reviews/edits, completes the case checklist and approves an exact content/recipient/profile revision. Rejections require notes. Edits invalidate approval. Approval records actor/time/hash/checklist. Export rechecks assignment, consent, current quotations and exact approval; simulated dispatch also requires approval. The local worker's broker reminders remain private.

## Privacy and measurement

The wizard's **Your data and privacy** disclosure exports saved data or deletes this journey, contacts, derived cases and associated grants/documents/jobs. Export excludes secrets and OTP material. Health-consent withdrawal removes sensitive current/history answers and derived cases. Intake expires24h; contacts/cases within7d; OTP10min; aggregate counts30d; chatbot-only feedback90d. See `docs/ux/SECURITY_PRIVACY_REVIEW.md` for boundaries and processor review.

Optional first-party funnel counts require server `JOURNEY_FUNNEL_ENABLED=true`, frontend `VITE_FUNNEL_ANALYTICS=true` and visitor Analytics consent. Both flags defaultfalse. Counts contain fixed event/step/mode/choice categories and day totals, no visitor IDs/answers. See `FUNNEL_REPORT.md`; totals do not establish unique conversion or user success.

## Actual API families and checks

Canonical routes are `/api/journey`, **not** the source brief's proposed `/api/v1`. Existing older research APIs remain separate. Families: profile/draft/history/undo; intake/turn; recommendations/view/explanation/questions; shortlist/selection/consents; verify; wizard/access/access-links; dashboard/quotations; broker; privacy; funnel. All sensitive state uses existing encrypted models and ownership checks. Additive migration head is `0008_funnel_counts`.

Checks: `uv run --project backend pytest backend/tests -q` (set DATABASE_URL=sqlite:// and empty GROQ_API_KEY for isolated tests); Ruff; frontend check/lint:uk/test/build; `npx playwright test -c playwright.uk.config.ts`; `npx playwright test -c playwright.wizard.config.ts`; original `npx playwright test`. Browser suites need the local API/worker. Restart only the isolated API between repeated/batched suites to clear in-memory limits; never loosen the limiter for tests. More than10 new sessions perIP/hour intentionally returns429, so run wizard suites in batches of at most10 session creations. Detailed commands/results and unverified checks are recorded in the phase ledger and QA checklist.

No real insurer, payment, policy, professional authorisation, provider delivery or production readiness is claimed. `build:production` must fail until the separate launch blockers are resolved and its removal explicitly approved.

## Light interface and WhatsMCP —25 October2026

The dark navy page surface and pale inherited card text are replaced by warm light surfaces with explicit dark card text, including hover/focus and dark OS preference. The centered topic column, restrained controls and stage navigation follow the Oscar reference while every question/value remains unchanged. Broker help docks with navigation; toolbar Ask Helm keeps chat available without covering controls.

WhatsMCP REST transport can send the OTP and the requested access link to an approved WhatsApp recipient. Configure the private backend/.env and explicitly start both API/worker with --allow-configured-sandbox; console remains the default. Setup and verification: docs/ux/LIGHT_UI_WHATSMCP.md. A link request bypasses reminder quiet hours, while later updates retain them. Queued provider acceptance is distinct from sent status and is never automatically resent. Credentials will be supplied later; this update does not claim live delivery.


## Actual WhatsApp verification entry point
Normal setup is `npm run api:prototype` plus `npm run worker:prototype`, using the private env configuration. The normal verification UI contains no fictional-number prompt, simulation banner or local reveal button. Missing provider credentials disable sends with an unavailable notice. Old console-mode challenges cannot be used after a transport switch; request a fresh real code. Automated tests retain `uk_test_server.py` and protected local-code helpers only for fixtures; stop the normal API before those test suites. See README and LIGHT_UI_WHATSMCP.md.
