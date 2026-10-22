# Preserved professional workspaces and unused files

The customer site remains in frontend/. Approved professional UI and three unreferenced files are archived here with their original repository-relative paths. No backend, migrations, real environment files, API contracts or auth helpers are moved or modified.

- AUDIT.md: historical Phase 1 classification, approved by the user before any move.
- MANIFEST.md: every actual move, dependency copy and whole original snapshot.
- MANIFEST.jsonl: the same operations as machine-readable JSON lines, including baseline Git blobs and content hashes.
- DEPENDENCIES.md: group packages, environment variable names, endpoints and shared files.
- broker-workspace/, provider-workspace/, claim-review/: preserved UI modules, their dedicated tests, dependency/config copies and extraction READMEs.
- _unused/: the approved unused hook, compatibility re-export and unused Lottie asset.
- _original_copies/: whole originals of files edited during the split; these are snapshots, not part of the active app.
- restore.sh: exact reverse git mv commands, with an all-moves preflight. Generated for review; NEVER executed during this task.
- verify_preservation.py: checks baseline coverage, archived content, original snapshots and protected paths without changing files.
- VERIFICATION.md: completed checks and practical limitations.

## Safest full restoration

The unchanged main branch and backup-before-split-20261022 both retain the original monorepo. With a clean working tree, `git switch main` returns to it. For a separate restoration branch use `git switch -c restore/before-split backup-before-split-20261022`. This preserves the cleanup branch and archive.

## Selective restoration

Review MANIFEST.md and restore.sh first. On a separate branch with a clean tree, `bash archive/restore.sh` would reverse only MOVE rows after confirming that every archive source exists and every original destination is absent. It does not overwrite files, remove copies or undo later edits. This script has NOT been executed.

Restoring page files alone does not re-register their routes. If original routing/styles/config are wanted, first preserve the current kept file at a new archive/_restore_checkpoints/<unique-name>/<original-path> using git mv, then git mv the corresponding whole original from _original_copies/ to its original path. Never copy over an existing file. Review config/test changes together and rebuild. Prefer the backup-tag branch above for a complete, consistent original checkout.

Each dashboard README describes the additional entry/auth/bootstrap work before the preserved modules become a standalone portal. They continue to call the same existing backend endpoints. Shared configuration files are reference copies; there are no real secrets or running services in these groups.

The two fixture-tour reports and scripts/start-prototype.ps1 remain in place under Needs my decision. No staff/admin frontend was found; broker operational controls and escalation live in claim-review.
