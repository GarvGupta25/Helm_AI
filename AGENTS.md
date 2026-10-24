# Shared repository workflow

- The shared source of truth is https://github.com/GarvGupta25/Helm_AI. The owner and a friend both work in this repository.
- Before starting work, inspect the current branch and local changes, fetch origin, and pull the latest branch updates with `git pull --ff-only` when the working tree permits it. Preserve existing local work and collaborators' changes.
- Make the smallest complete change and run the checks appropriate to it. Use the root README for the prototype setup and isolated demo API.
- When work is finished, commit only the intended files, fetch again, integrate any new remote changes, and push the finished commits to this repository. Do not leave completed changes only on the local machine.
- Never force-push shared history or commit credentials, local environment files, runtime databases, or generated dependency folders. Report a blocked push clearly.


## Guided quote redesign — 25 October 2026

The current phase plan is `docs/ux/GUIDED_JOURNEY_PLAN.md`; audited contracts and decisions are in `docs/ux/WIZARD_SPEC.md`, captured design tokens in `docs/ux/DESIGN_TOKENS_CAPTURED.md`, and actual per-phase results in `docs/ux/WIZARD_PROGRESS.md`. The owner explicitly authorised progressing through phases without repeated approval requests. Preserve the English-only interface, legacy fallback, deterministic engine and professional authorisation. Reuse existing `/api/journey` services rather than create a second `/api/v1` journey.

Wizard Phase 1: set `VITE_QUOTE_WIZARD=true` before starting Vite/building to enable per-step `/get-cover/quote/*`. Default false preserves legacy; `/get-cover/legacy-intake` is always available. `playwright.wizard.config.ts` starts the flag-on test frontend at 4175; normal preview remains4174. Autosave writes drafts, confirmation alone changes ranking inputs.

Wizard Phase5: flag-on `/get-cover/plans` is a separate10-option page with view-only filters. `/get-cover/compare` is no longer a redirect when the flag is on; compare/detail/selection UI follows in Phases6–7. Legacy flag-off routes remain. The API defaults to3 for compatibility, with validated `?limit=10` for wizard runs.

Wizard Phase7: flag-on `/get-cover/compare` and `/get-cover/selection` are separate pages. The canonical reviewed receipt is `/api/journey/selection`,1–3 plans and exact named sharing consent. It does not create a policy/payment/account link or contact an insurer. `/api/v1/quotation/confirm` remains the isolated legacy single-plan demo contract.

Wizard Phase8: `/get-cover/verify` and `/get-cover/verify/code` require the current consented selection. `uk_test_server.py` forces console verification; real network transports are allow-listed, server-configured sandboxes only. See `docs/ux/VERIFICATION_SETUP.md`; never expose provider credentials or codes. Additive migration0007 adds encrypted rolling OTP windows.

Wizard Phase9: `/get-cover/access` creates a24/48-hour private link after current verified selection; `/my-quotes` is the tabbed dashboard alias. Tokens use fragments and deliberate exchange; they never enter request paths. The existing `/quote-dashboard` remains compatible. The isolated worker defaults console-only; explicit --allow-configured-sandbox is required for configured allow-listed notifications.
