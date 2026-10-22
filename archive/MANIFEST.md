# Preservation manifest

Safety tag: `backup-before-split-20261022`. Approval received after the Phase 1 audit. MOVE rows have exact inverse commands in restore.sh; COPY and ORIGINAL-SNAPSHOT leave the source in place. All content digests are SHA-256 of original on-disk bytes before the operation. Baseline Git blob IDs are also recorded in MANIFEST.jsonl to account for line-ending normalization. This table is append-only.

| Operation | Original path | Archive path | Reason | Group | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| ORIGINAL-SNAPSHOT | `frontend/src/main.tsx` | `archive/_original_copies/frontend/src/main.tsx` | Whole original preserved before editing retained file | _original_copies | `2e02ac429a64b3e5ff88540207dd80ef5ab59c13837cbd5680663534a8004451` |
| ORIGINAL-SNAPSHOT | `frontend/src/styles.css` | `archive/_original_copies/frontend/src/styles.css` | Whole original preserved before editing retained file | _original_copies | `280de628ea02ba04e59616e0c1a53b0b4c61fb988ae1ac7e095d05a36bfc17c8` |
| ORIGINAL-SNAPSHOT | `frontend/src/foundation.css` | `archive/_original_copies/frontend/src/foundation.css` | Whole original preserved before editing retained file | _original_copies | `7040d4c0f00938d618f7b7a4ac263c516ff68990c9a0d944927beb149249ac48` |
| ORIGINAL-SNAPSHOT | `frontend/tsconfig.json` | `archive/_original_copies/frontend/tsconfig.json` | Whole original preserved before editing retained file | _original_copies | `f7710c1db9c890ba329c9931e1fee981fa960c313fa08fd500ee3a25876652fe` |
| ORIGINAL-SNAPSHOT | `frontend/vite.config.ts` | `archive/_original_copies/frontend/vite.config.ts` | Whole original preserved before editing retained file | _original_copies | `f9ff678a7d0cb6bdba58ab8541e73f54743e8c3db8871f744bf45b2030644079` |
| ORIGINAL-SNAPSHOT | `playwright.config.ts` | `archive/_original_copies/playwright.config.ts` | Whole original preserved before editing retained file | _original_copies | `048886e9e0a03d9fb0a2c1ef0e6d4fc914136495661c4dba815cfe5b70ade2b0` |
| ORIGINAL-SNAPSHOT | `README.md` | `archive/_original_copies/README.md` | Whole original preserved before editing retained file | _original_copies | `6f2bd280e6207c692a91c636f4007ea7787bea043e412994a033845d899ed367` |
| ORIGINAL-SNAPSHOT | `frontend/.env.example` | `archive/_original_copies/frontend/.env.example` | Whole original preserved before editing retained file | _original_copies | `2edcf2e7a96b12e6398fe802e9340770ca7480fb5c5da976bed12c73cee49778` |
