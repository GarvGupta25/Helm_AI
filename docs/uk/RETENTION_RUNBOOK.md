# Retention and migration operations

No live database has been modified. Before applying a migration, take and verify an encrypted database backup, capture schema version/row counts and rehearse on a restored copy. Do not relabel historical monetary values as another currency. Reconciliation and owner approval are required for any financial conversion.

UK schema migration: `alembic -c backend/alembic.ini upgrade head` using an explicitly configured DATABASE_URL. Seed: run `backend/scripts/uk_demo.py` only against an approved demo database. Downgrade drops new UK tables, so export and verify UK records first; never use downgrade as a routine user-data rollback.

Proposed retention: quote snapshots seven days; public intent metadata and demo tickets 30 days. Expiry blocks access immediately. The maintenance command below performs bounded deletion of these demo-only records, never historical policies or accounts. Schedule and verify it before launch. Consent records associated with expired demo quotes are removed with the quote; real regulatory retention needs separate approval.

Run `python backend/scripts/uk_retention.py --dry-run` first. The destructive `--apply` switch is intended only for the approved demo database. The assistant has not executed it against user data.
