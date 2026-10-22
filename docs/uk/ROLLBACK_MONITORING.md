# Soft launch, monitoring and rollback draft

Current decision: NO-GO for real insurance distribution. Demo preview only.

Before a demo release: verify permanent demo banner, no false credentials, no real purchase, configured contact expectations, synthetic dataset and public-source guard. Publish only after owner review; this task pushes source commits, not a hosted deployment.

Before a real release: resolve every blocker in LAUNCH_READINESS.md, validate a restored database backup and rehearse the additive migration on staging. Named owners must approve legal copy, transfers, product facts, support staffing and Consumer Duty research.

Monitor a consenting population with aggregate metrics: quote HTTP failures/latency, form validation friction, keyboard errors, complaint intents, support backlog, safety routes, quote expiry and deletion jobs. No raw health or chat content in dashboards. Define alert owner, thresholds, runbook and coverage hours before launch. No production dashboard is claimed to be installed.

Rollback application: stop the release, restore the previously approved deploy artifact, and disable new sales. Use Git revert commits on shared main rather than force-pushing. `uae-final` is a source backup, not an approved UK production release. Do not roll user data back blindly or relabel money units. Preserve forward audit records and reconcile any changed data before restoration. Database downgrade drops new UK tables and needs an explicit export/restore plan; it is not the default rollback.

Incident exercise: missing rate row; expired token; unavailable support; assistant abuse; broken consent storage; policy mismatch; deletion job failure; browser accessibility regression. Record detection, user impact, mitigation, owner and follow-up date.
