# Phase reports — implementation checkpoints and outstanding acceptance

Date: 22/10/2026. Branch: `main`, per the owner's explicit request. Every phase has an engineering checkpoint, but **not all phase acceptance criteria are complete**. No launch approval or owner sign-off is inferred. The source brief was treated as the specification, not as proof that its legal assumptions were correct.

Screenshots and automated reports in `evidence/` describe the final working tree when captured, not every historical phase. Per-phase Lighthouse/a11y captures were not produced and are not backfilled as if they had been. Exact scores are in `PERFORMANCE_ACCESSIBILITY_REPORT.md`; missing measurements remain unverified.

## PHASE 0 REPORT — 8a48f3d
- Summary: restored local repository metadata from matching remote history; preserved baseline `uae-final` locally/remotely; added UK config, source inventory and decision documents.
- Files: `frontend/src/market/uk.config.ts`, `backend/app/market/{__init__,uk}.py`, `scripts/uk_inventory.py`, `docs/uk/{CHANGELOG_UK,OPEN_QUESTIONS,ASSET_LICENCES,COMPLIANCE_PLACEHOLDERS,REFERENCE_DELTA,ARCHITECTURE_DECISIONS}.md`, `uae_leftovers.csv`.
- Acceptance: ✔ baseline tag; ✔ config compiles; ✔ tracked-source inventory; ✔ reference delta document; ✔ phase-0 code does not change app behaviour. ✘ live browser timing capture/recording, eyedrop measurement and competitor audit.
- Leftover scan: 353 matches at baseline. Current inventory remains nonzero.
- Screenshots/Lighthouse: not run for this phase.
- Deviation: remained on main because the user explicitly requested main, overriding the suggested branch.
- Open questions: legal identity, live/demo intent, brand/media and compliance owners; see OPEN_QUESTIONS.md.

## PHASE 1 REPORT — 5314de0
- Summary: scoped tokens, self-hosted fonts, Radix modal/tabs/tooltips, labelled form controls, focus and motion styles.
- Files: `frontend/src/ui/{tokens.ts,primitives.tsx,uk.css,README.md}`; dependencies completed in phase 2; unit tests added in phase 10.
- Acceptance: ✔ current type-check; ✔ reduced-motion and focus styling; ✔ five meaningful primitive tests. ✘ full Storybook/Ladle catalogue, per-primitive stories/screenshots and independent contrast audit.
- Leftovers: legacy inventory remains nonzero; no whole-repository clearance.
- Screenshots/Lighthouse: no phase-specific evidence; see final Home/About evidence at 375/768/1280/1920.
- Deviation: used native labelled controls and details for simple interactions alongside Radix.
- Open questions: approved final brand assets and complete component catalogue.

## PHASE 2 REPORT — ceb1cd1
- Summary: five navigation groups, mega-menu panels, mobile dialog, search, footer, external interstitial and cookie preferences. Public pages render without an API dependency.
- Files: `frontend/src/uk/{Shell.tsx,navigation.ts,PublicApp.tsx,site.css}`, original entry point, index.html and package manifests.
- Acceptance: ✔ tested keyboard open/Esc; ✔ expanded states; ✔ mobile dialog/Esc/focus; ✔ external-link guard; ✔ equal cookie accept/reject; ✔ no optional scripts; ✔ visibly unresolved regulatory details. ✘ measured visual parity, first-load brand animation and every gesture/focus-leave case.
- Leftovers: legacy customer code and archives retained; final UK public-source guard is separate.
- Screenshots/Lighthouse: final evidence only.
- Deviation: English only, with truthful language-support limits; no unreviewed Welsh content or false authorisation.
- Open questions: languages, live contact route and approved status disclosure.

## PHASE 3 REPORT — 2f66524
- Summary: licensed responsive family-photo hero, cover categories, how-it-works, demo stats, tabs, plan preview, renewal notes, scenario explanations, values and FAQs.
- Files: `frontend/src/uk/{Home.tsx,home.css,PublicApp.tsx}`, `frontend/public/assets/uk/family-*.webp`, asset ledger.
- Acceptance: ✔ responsive hero; ✔ clear demo labels; ✔ no unverified badges; ✔ no invented savings; ✔ tax facts sourced. ✘ exact word-mask/parallax choreography, all requested motion effects, approved captioned film and field Web Vitals.
- Leftovers: not a whole-repository purge.
- Screenshots: `evidence/home-{375,768,1280,1920}.png`; current capture date/version reflected in the evidence commit.
- Lighthouse: see measured report; do not infer passing target scores.
- Deviation: an explicit written explainer replaces the unavailable owner-approved video; mini-calculator routes to actual server demo prices instead of inventing a range.
- Open questions: real media approval, verified customer data and real adviser availability.

## PHASE 4 REPORT — bdeb15f
- Summary: About narrative, demo statistics, roadmap, observer-driven sticky original illustration, Embla values, truthful credentials disclosure and footnotes.
- Files: `frontend/src/uk/{About.tsx,PublicApp.tsx}` with shared Home primitives/styles.
- Acceptance: ✔ six roadmap steps; ✔ keyboard-focus illustration state; ✔ mobile value carousel status; ✔ footnote/back links. ✘ exact nine-section reference parity, three real photos, count-up/crossfade/pinned GSAP choreography.
- Leftovers: historical inventory remains nonzero.
- Screenshots: `evidence/about-{375,768,1280,1920}.png`.
- Lighthouse: see measured report.
- Deviation: omitted an unverified founder quote and false credentials; roadmap explicitly is not company history.
- Open questions: real milestone dates, verified credentials and quote.

## PHASE 5 REPORT — 65c451b
- Summary: reusable content templates, all nine cover-category routes with exclusions, glossary, FAQs, fictional finder, comparison and audience/support content.
- Files: `frontend/src/uk/{Content.tsx,PublicApp.tsx}`.
- Acceptance: ✔ navigation destinations have routes; ✔ exclusions on cover categories; ✔ finder filters and clear fictional locations; ✔ glossary deep links. ✘ full editorial review, all-page metadata uniqueness/canonicals, automatic glossary tooltips, article TOCs/progress and readability/comprehension verification.
- Leftovers: public replacement is additive; historical content remains.
- Screenshots/Lighthouse: no phase-specific captures.
- Deviation: unavailable portal/onboarding/training services state that they are disabled rather than pretending a submission occurred.
- Open questions: approved long-form content and genuine hospital network data.

## PHASE 6 REPORT — e2f9d44
- Summary: structured quote wizard, validated UK data, server pricing/IPT, comparison drawer, needs statement, consent journal, capability resume and idempotent zero-payment confirmation.
- Files: `backend/app/market/{quote,models,router}.py`, main router registration, `backend/tests/test_uk_quotes.py`, `frontend/src/uk/{QuoteWizard.tsx,quote.css,PublicApp.tsx}`. Phase 10 switched endpoint pricing to the seeded rate rows.
- Acceptance: ✔ browser demo journey completes; ✔ integer-pence reconciliation/rounding; ✔ required consent booleans; ✔ disclosed ranking; ✔ server-owned frozen results and idempotency. ✘ approved IPIDs, actual Stripe/GoCardless test integration, email magic links, account linkage and manual screen-reader completion.
- Leftovers: old customer/financial contracts not migrated.
- Screenshots/Lighthouse: final public evidence only; browser test output includes quote journey.
- Deviation: written key facts explicitly are not an approved IPID; no money or policy is issued. Resume is browser-session only.
- Open questions: carrier documents, payments, secure email/account integration and advice permissions.

## PHASE 7 REPORT — a07df59, 558cbeb
- Summary: reviewed UK guidance, safety/PII/advice/medical routing, intent-only audit and demo support references; 14 specified cases plus 200 adversarial variations.
- Files: `backend/app/public_assistant.py`, main handler, public assistant/UK tests, launcher/panel components and CSS.
- Acceptance: ✔ 14 required intent tests and 200 attack variations; ✔ no model inference/raw transcript retention; ✔ support reference linked to audit; ✔ non-spoofable in-process client limit. ✘ Groq/LangGraph multi-turn public chat, full RAG/tool catalogue, live dashboard/callback delivery and scheduled retention operations.
- Leftovers: market-contamination inputs exist deliberately in guardrail tests/classifier; responses stay UK scoped. Entire repository is not purged.
- Screenshots/Lighthouse: final browser chat test; no per-phase score.
- Deviation: reviewed deterministic knowledge mode instead of unsupervised raw-text inference; crisis reply uses emergency/NHS signposting, without claiming an independently configured UK helpline service.
- Open questions: approved live crisis resource configuration, transfer approvals and staffed escalation.

## PHASE 8 REPORT — fe9362a
- Summary: additive reversible migration, 30 fictional plans, 23,100 rates, idempotent seed and deterministic UK servicing function.
- Files: `backend/app/market/{models,seed,quote}.py`, servicing.py, Alembic config/env/version, demo setup script, tests and Python packaging/lockfile.
- Acceptance: ✔ migration up/down on isolated SQLite; ✔ idempotent 30-plan/rate seed; ✔ tested financial rules. ✘ all legacy columns/prompts/contracts converted, Postgres backfill rehearsal, schemathesis suite and historical professional models migration. Coverage figures are recorded separately.
- Leftovers: nonzero historical inventory retained intentionally pending safe conversion; no currency relabelling or data deletion.
- Screenshots/Lighthouse: backend phase; no phase-specific browser scores.
- Deviation: existing datasets and archived dashboards preserved; no live database migration executed.
- Open questions: approved data migration/reconciliation plan and real deployment database.

## PHASE 9 REPORT — c322634
- Summary: truthful draft legal pages, DPIA/ROPA, Consumer Duty pack, retention runbook/command and demo/live-release guards.
- Files: Legal.tsx, PublicApp.tsx, package build scripts, uk-release-guard.mjs, compliance docs, retention script and CI guard.
- Acceptance: ✔ compliance review materials; ✔ public-source guard in CI; ✔ live build fails closed; ✔ demo status disclosed. ✘ repository-wide zero leftovers, approved legal copy and actual compliance/DPO/financial-promotion sign-off.
- Leftovers: 351 matches at the phase-9 checkpoint; use current CSV for latest count. Not zero.
- Screenshots/Lighthouse: final legal route axe/browser evidence.
- Deviation: normal build is a labelled demo; live build is blocked. Archives are not silently excluded from a claimed whole-repository result.
- Open questions: all legal identity, product and processor approvals.

## PHASE 10 REPORT — 97f72a1
- Summary: public/customer bundle separation, lazy public routes, Latin font subsets, local Lottie runtime, contrast fixes, lint/unit/browser suites.
- Files: main/CustomerApp, PublicApp, uk.css/hardening.css, launcher, package manifests, tests, configs, CI and test-server script.
- Acceptance: ✔ four-width overflow checks; ✔ tested reduced motion, keyboard, privacy and quote/chat flows; ✔ five unit tests; ✔ scoped frontend and backend lint. ✘ full manual screen-reader/high-zoom/device matrix, every motion requirement and all measured performance budgets. Latest axe and Lighthouse outcomes are in the evidence report.
- Leftovers: UK public modules pass scoped guard; historical paths remain in the inventory.
- Screenshots: eight final Home/About viewport captures.
- Lighthouse: actual reports in evidence; no invented 90+ scores.
- Deviation: observed CSS inheritance failures were fixed and retested; no manual audit is claimed.
- Open questions: independent accessibility and real-device testing.

## PHASE 11 REPORT — final evidence/readiness checkpoint
- Summary: browser suite, test API, regression checks, comprehension-research pack, security review and rollback/monitoring runbook. Real launch is NO-GO.
- Files: tests/uk, CI, docs/uk/evidence, COMPREHENSION_TESTING_PACK.md, SECURITY_REVIEW.md, ROLLBACK_MONITORING.md, LAUNCH_READINESS.md, this report and evidence summary script.
- Acceptance: ✔ automated tests/review pack prepared; ✔ honest go/no-go memo and rollback plan. ✘ all Part D items, 15+ real UK sessions/retests, full ASVS L2/load assessment, manual device matrix and compliance/legal/DPO signatures.
- Leftovers: current CSV is nonzero; zero-leftover requirement is unfulfilled.
- Screenshots/Lighthouse: see final evidence and PERFORMANCE_ACCESSIBILITY_REPORT.md.
- Deviation: real-user research and professional approval cannot be fabricated or substituted with automated tests.
- Open questions: named owners, recruitment and completion of outstanding engineering/operational acceptance items above.
