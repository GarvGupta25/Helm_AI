# Guided journey phase ledger

Source: GUIDED_JOURNEY_PLAN.md; owner authorised autonomous phase progression on 25 October 2026. Earlier stop/approval text is superseded, not a blocker.

## Phase 0
- Read plan and embedded master prompts, prior journey master prompt, AGENTS, overview, workflow/research/archive/readiness/chat notes and current schema/routing/services.
- Verified schema and seven-essential contract; recorded current-vs-stale-plan differences, exact tokens, field inventory, route map, reuse and D1–D9 in WIZARD_SPEC.md.
- Existing shared branch clean and fetched/pulled; no application source changed.
- Baselines and execution results recorded below before committing.

Remaining phases 1–13 are pending. No live delivery or manual-device claims.

Phase 0 verification: 7 baseline captures passed; the eighth encountered the existing session-creation rate limit and will be retried with a shared test session. Seven captured views (1440/375, light/dark media, LTR/structural RTL) under docs/ux/baselines. Current quote has no actual dark skin; baseline captures this gap. No application source was modified. UI/UX Pro Max search retrieved progressive disclosure and accessible controls; existing Helm palette and Inter/Instrument Serif retained over generic generated suggestions.

Phase 0 baseline correction: first run was 7 passed / 1 rate-limited, not eight successful tests. Restarted only the owned isolated API, preserved the limiter, and captured all eight layouts in one private session: 1 baseline matrix test passed (8 screenshots), 10.9s. No capability/code/token is visible in captures.

## Phase 1 — shell, routes, draft and choice
- Added flag-gated WizardApp, registry/guards, four-stage progress, focus handling, sticky navigation, mode choice, session mode preference and saved-state feedback.
- Reused canonical encrypted draft/revision/hash endpoints; serial coalesced autosave, explicit flush before navigation, retry state and unsaved-refresh warning. No second profile store. Question inputs arrive in Phase 2; AI is explicitly a placeholder until Phase 4.
- Flag-off one-page form preserved; /get-cover/legacy-intake remains explicit fallback.
- Verification: 14 frontend unit tests passed (including registry/guards); TypeScript and scoped lint passed. Wizard browser shell/guard/refresh/mode-switch/fallback + scoped axe: 1 passed,19.5s. A timezone-boundary test initially failed due to a UTC-derived fixture date; fixed by local-date helper, rerun passed.
- Pending in subsequent phases: actual question-input autosave path, full restore/race tests, physical screen-reader/mobile tests. No live integration exercised.

## Phase 2 — mandatory topics and checkpoint
- Re-read source plan/master prompt and canonical contract. Added consent/withdrawal, household age/DOB/smoking cards, searchable region, constrained dates, budget/excess/hospital chips, inline hard preferences and all11 benefits across3 screens.
- Exact field keys, values and server validation preserved. Final review explicitly distinguishes no essential benefits from unanswered. Confirming essentials creates the canonical version before the checkpoint.
- Fixed a server-default normalization autosave loop found by browser checks; regression test proves a normalized acknowledgement stops resaving.
- Verification:15 frontend unit tests passed; TypeScript/scoped lint passed. All3 wizard browser tests passed24.3s, including actual API-backed desktop1440/mobile375 mandatory path, saved refresh, payload assertions, light/dark and scoped axe. First browser retries exposed normalization and too-fast test navigation; fixed application normalization and made test wait for route changes. Repeated sessions hit existing limiter; restarted only isolated API before final run, no limit change.
- 60-persona canonical form/extractor contract replay passed (1 pytest,0.22s): seven common fields exactly match. This is schema/extractor replay, not60 full browser journeys. Physical devices/screen readers and live providers unverified.

## Phase 3 — optional details, review and early plans
- Re-read full source plan and Phase3 prompt. Added the5 optional screens with exact values, help, explicit Skip-to-null behavior, hard toggles, persistent Show my plans, grouped review, exact edit-return links, saved draft, version history and Undo.
- Optional answers never gate recommendations. Skipping clears an earlier answer to not-answered instead of converting to no. View changes require a new canonical confirmation.
- Moved the public launcher above the sticky controls after screenshot review found overlap at375px.
- Verification:2 actual API browser journeys passed16.2s at1440/375: skip all optional fields, obtain a stored recommendation run, edit-return, create another confirmed version and Undo/history. Scoped lint and TypeScript passed. Plans destination UI is implemented in Phase5; current navigation alone is not claimed as a finished plans page. Manual devices and screen readers remain unverified.

## Phase 4 — server-controlled guided interviewer
- Re-read source plan/master prompt. Added /api/journey/intake/turn using the existing capability and versioned profile. Server chooses mandatory-first questions; direct structured inputs confirm immediately with Undo. Text becomes an encrypted, revision-bound proposal and requires explicit confirmation.
- Added IntakeLLM protocol, deterministic parser, consent-gated configured Groq extractor with strict schema/current-question checks and failure fallback, and an explicit fallback-only second-provider extension point. No provider can set scores, prices, eligibility or consent. Optional skip is distinct from no.
- UI has quick replies, exact numeric/date controls, optional Skip/Show plans, reviewed proposals, bounded current-question state, Stop/Retry, summary and mode switching. Public assistant unmounts in guided mode. Fixed stale question rendering during route transitions and sticky-control overlap found by browser tests.
- Verification:3 focused backend tests passed0.54s (including60-persona contract and injection/scope/provider-timeout/review checks); Ruff, TypeScript and scoped lint passed. Final2 guided browser journeys passed17.9s, desktop1440/mobile375, all essentials, mode switch and same saved profile.
- Evaluation script wizard_evaluate.py:60 synthetic personas,540/540 canonical section matches (100%), average7 mandatory turns,100% deterministic fallback,0 provider calls. This measures controlled schema/extractor replay, not live LLM accuracy or medical/regulatory quality. Live provider calls, second provider and physical devices remain unverified.

## Phase 5 — separate plans page and view filters
- Re-read source plan/master prompt. Added /get-cover/plans with desktop sidebar, mobile filter dialog, sort, eligible-count announcements, detailed cards, best-match/lowest-price labels, locked-hard-rule explanation, explicit save-to-answers confirmation, max3 compare/selection and a sticky tray.
- Extended canonical recommendations with validated ?limit=1..10 (default3 retained for existing callers). Wizard asks for10; top3 remain byte-for-byte equal to the original diverse shortlist. Remaining variants are eligible, deterministic ranked alternatives; costly simulation remains on the first3.
- /runs/:id/view narrows/reorders stored eligible options only and does not mutate profile/run. Required unknown existing-condition cover fails, and no display filter relaxes confirmed rules. Saving filters requires explicit confirmation and a new profile version; adding health priorities still needs existing processing consent.
- Verification:4 focused backend tests passed5.14s (existing engine/API regressions plus extended list/view immutability); Ruff passed. Final2 desktop/mobile browser tests passed31.7s:10 cards, optimistic persisted selection/max3, empty view/reset, unchanged version, scoped axe and no overflow. TypeScript/scoped lint passed. First browser run exposed delayed checkbox feedback; added optimistic state with rollback on error.
- Detail/compare/review destinations are staged for Phases6–7. Physical device performance and a sub300ms deployed network SLA are not claimed; UI requests are debounced180ms.

## Phase 6 — plain-English detail and policy Q&A
- Re-read source plan/master prompt. Added frozen-run detail routes and server-generated sections: fit, included/not included, payment/scenarios, conditions, hospitals and methodology. Component percentage bands are deterministic; raw scores/alpha are behind Show the numbers.
- Reused six integer-pence scenarios and existing grounded policy assistant, with visible source fields, modal focus handling, refusal of unsupported facts and a per-policy request limit. Existing conditions and missing waiting-period evidence remain explicit.
- Verification:52 backend tests passed7.86s, including50 question cases across3 policy snapshots with expected facts/citations/refusals (150 corpus replays), plus bands/template determinism. Ruff, scoped lint and TypeScript passed.
- Final detail browser results recorded below. An initial locator failure exposed an overlong accessible input name including helper text; added an explicit concise accessible name. No live provider or physical-device/screen-reader claim.
Phase6 final browser verification: 2 passed,17.2s at1440/375; separate detail sections, numbers hidden, premium citation, unknown-question refusal, back to preserved plans view, and scoped axe.

## Phase 7 — comparison and consented selection
- Re-read source plan/master prompt. Replaced the flag-on compare redirect with a2–3-column comparison and a server-generated Main differences summary. List/detail/compare choices share the persisted canonical shortlist and the three-plan limit.
- Added reviewed selection with exact shared profile, named insurer consent and optional broker consent (initially unticked). /api/journey/selection accepts1–3 eligible plans, rejects stale/foreign/conflicting selections, reuses an identical receipt and rejects withdrawn consent. It records no payment/policy/account linking. The older single-plan research receipt remains isolated for legacy compatibility.
- Verification:3 parametrized backend tests passed5.58s for1/2/3 choices,4th rejection, isolation, stale version, conflicting choice, idempotency and withdrawal. Ruff after formatting fixes, TypeScript and scoped lint passed. Final2 desktop/mobile browser flows passed25.9s: compare facts, choose from comparison, consent gate, persisted receipt on refresh. Verification destination is built in Phase8, not claimed complete at this gate.

## Phase 8 — international contact and controlled OTP delivery
- Re-read source plan/master prompt and checked primary provider examples. Added phone/email pages, country calling codes, explicit verification-only consent, six-digit paste/advance inputs, countdown, attempts feedback, private local inbox and refresh restore.
- Added /api/journey/verify start/check/status/config with selection binding, encrypted destination, salted HMAC code,10-minute expiry, five committed guesses, consumed/replaced-code checks, per-number/session persisted rolling3/hour windows,60-second cooldown and unchanged10/IP/hour limiter. New-flow contacts cannot use the legacy verifier. Codes exist only in bounded expiring memory for console mode, never new-flow database/log plaintext. Added migration0007 and idle-window cleanup.
- Added official WhatsApp authentication-template and TLS SMTP transports behind an interface and exact allowlist, with configuration/error handling. The isolated API explicitly forces console. No real WhatsApp/email was sent and no live ownership/provider integration is claimed. See VERIFICATION_SETUP.md for configuration and external prerequisites.
- phonenumbers9.0.41 is the sole new dependency, justified in DEPENDENCIES.md for international validation explicitly required by the plan; no frontend dependency added.
- Verification:7 focused verification/contact/retention tests passed7.69s; fresh/downgrade/upgrade migration test passed in an earlier4-test run; final legacy-route bypass assertion rerun separately. Mock official request payload, normalisation, hashing/encryption, isolation, consent/CSRF, cooldown, send cap, expiry, attempts and replay checks passed. Ruff, TypeScript and scoped lint passed. Both1440/375 browser OTP flows passed13.8s (console email fallback, no live messaging). PostgreSQL concurrent execution and actual transports remain unverified.
