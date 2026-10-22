# Split verification

Date: 2026-10-22 (client timezone Asia/Calcutta). Safety baseline: backup-before-split-20261022 at 8140750cf7fdae91443f9fe59938f41f03fb57b7. Working/publishing branch: cleanup/split-main-site. The user approved the Phase 1 classification, then explicitly requested committing/pushing the changes to GitHub. main is not merged or changed.

## What stayed

All 14 public marketing/help/legal route patterns and the public chatbot; Login signup/recovery/reset modes; customer overview, profile/intake/conversation, quotes, application confirmation, marketplace comparison/selection/activation status, policies, claims/status/evidence/appeals, servicing, payments, documents and nearby-care map remain. Existing customer feature modules and API/auth helpers are unchanged. Customer requests for human review and provider responses remain supported by the existing backend.

## What moved

| Group | Moved baseline files | Shared/config/support copies |
| --- | ---: | ---: |
| broker-workspace | 3 | 15 |
| provider-workspace | 8 | 15 |
| claim-review | 3 | 15 |
| _unused | 3 | 0 |
| Total | 17 | 45 |

Eight retained files have whole baseline originals in _original_copies/ before their edits: main.tsx, styles.css, foundation.css, frontend tsconfig/Vite config, Playwright config, root README and frontend/.env.example. Actual paths/hashes and all move/copy reasons are in MANIFEST.md and MANIFEST.jsonl. Professional-only CSS selectors are preserved in the copied originals; 110 such selector branches were removed from active styles.css and 9 from foundation.css. Shared customer .broker-approved, .claim-flag and .provider-map styles remain.

## Completed checks

| Check | Result |
| --- | --- |
| npm ci at root and frontend | Passed; package manifests and lockfiles unchanged |
| npm run build | Passed: TypeScript build and Vite production bundle |
| npm run check | Passed |
| frontend npm exec -- tsc --noEmit | Passed |
| npm run test:e2e | 17 passed across 5 active spec files |
| Broker/provider/staff portal tests with configured HTTPS URLs | 3 passed; links target configured portals |
| Same portal tests with javascript, malformed and relative URLs | 3 passed; invalid links omitted, guidance/sign-out retained |
| Account-role pending/error/professional states | Browser tests confirm customer/internal data is not loaded before member access is confirmed; retry and sign-out work |
| Archived route fallback | Browser test covers /app/broker, /app/broker/claims, /broker/claims and /provider |
| Development server | Started by Playwright; browser tests exercised the real Vite UI with deterministic API boundaries |
| Kept routes/imports/navigation | 22 path declarations, all baseline customer paths retained; relative imports resolve and literal navigation targets match registered paths |
| Compiler boundary | All 38 kept TS/TSX/declaration files included; zero archived files included |
| Production bundle boundary | No /api/broker/ or /api/provider/ endpoint calls in generated JS; active robot.json included, archived helm-assistant.json excluded |
| Main test boundary | Exactly 17 tests across 5 kept specs; no archived broker/provider/claim-review spec discovered |
| Archive build/watch/test boundaries | TypeScript excludes archive, Vite watcher ignores it, Tailwind @source not excludes it, Playwright ignores it; active customer source still compiled |
| ESLint/Vitest | Not configured in this revision; no checks hidden or disabled |
| git diff --check | Passed |
| restore.sh | Exists; bash -n syntax check passed; exact inverse of all 17 manifest moves; NOT executed |

Vite reported a non-failing chunk-size warning for a JavaScript chunk over 500 kB. No package removal or unrelated chunk refactoring was performed.

## No-loss proof

`python archive/verify_preservation.py` checks every safety-tag path, all archive records, preserved originals, current imports/links and exact reverse-move commands without changing files.

- Safety-tag baseline: 187 files.
- Files remaining at original paths: 170.
- Exact manifest-mapped archive moves: 17.
- Missing baseline files: **0**.
- Verified archive records: 70 (17 moves + 45 copies + 8 original snapshots).
- Archive records matching original on-disk SHA-256 bytes: 70/70 in this checkout.
- Every archived Git blob matches the safety-tag blob (also supports Git line-ending normalization on future clones).
- Every changed retained baseline file has its whole original preserved.

The verifier also asserts zero diff for backend/, supabase/, api.ts/auth helpers, package manifests/lockfiles, both docs fixture reports and scripts/start-prototype.ps1. The original Login implementation is checked byte-for-text against its snapshot and is unchanged.

`git diff --stat main -- backend` and `git diff --stat main -- supabase` both produced empty output: zero diff. Database schema/RLS, migrations and backend contracts are unchanged. Real environment files and backend/.env.example were not modified. The explicit requested exception is frontend/.env.example: only blank portal URL names and an explanatory comment were appended; its entire original is preserved.

## Needs my decision / practical limits

Both docs fixture-tour JSON reports and scripts/start-prototype.ps1 remain in place. No standalone staff/admin UI exists in the baseline. The professional archives are extraction kits with original modules/tests, shared files and setup checklists; each future portal still needs its own frontend entry/session/role-guard bootstrap and deployment configuration as described in its README. No portal was deployed and no real portal URL is assumed.

Backend runtime tests, real Supabase/database operations, live insurer/payment integrations and physical-device tests were not run for this frontend-only restructuring. The existing backend and tests remain untouched. Browser tests mock API boundaries and validate the real customer UI.

## Review and restoration

Publishing target: https://github.com/GarvGupta25/Helm_AI/tree/cleanup/split-main-site. The cleanup branch and safety tag are pushed explicitly; main is not merged. Final remote commit/tag verification is reported in the chat after publication.

Review:

```sh
git diff --stat main..cleanup/split-main-site
git diff main..cleanup/split-main-site -- frontend/src/main.tsx
python archive/verify_preservation.py
```

After review, a user-chosen merge can be performed locally with a clean working tree:

```sh
git switch main
git merge --no-ff cleanup/split-main-site
```

No merge is executed by this task. To return to original main before any user merge, use `git switch main`. For a preserved original-state branch use `git switch -c restore/before-split backup-before-split-20261022`. For selective file restoration, review README.md and restore.sh; preserve current mixed files at new checkpoint paths before restoring their original copies. Never overwrite newer work. restore.sh itself was not executed.
