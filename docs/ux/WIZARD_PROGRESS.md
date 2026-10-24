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
