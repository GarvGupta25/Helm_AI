# Synthetic research workspace: Phase 0

The existing React 19/Vite/FastAPI application already has a UK demo quote journey, 30 fictional products, integer-pence pricing, guarded public guidance and additive UK tables. Preserve those contracts and all historical customer records. No US marketplace API or real policy data will be introduced.

## Design and acceptance sequence

1. Generate 12 fictional insurers × 8 families × 6 meaningful excess/network variants (576), 10,000 profiles, 3,000 chronological histories and 60 reviewable personas. Seeded JSON exports and YAML-compatible JSON configuration carry immutable lineage. Validate counts, references, monotonicity and chronology before matching.
2. Add isolated `research_*` PostgreSQL-compatible catalogue/state tables and an Alembic revision. Import generated catalogue only through an explicit administrator CLI. Runtime API fails closed if catalogue is absent. No public generation endpoint.
3. Price in integer pence; simulate six explicit scenarios with covered/uncovered costs, caps and annual excess. Test hand vectors before scoring.
4. Standard weights 30/20/15/15/10/10; contextual substantive weights 25/20/15/10/10/10 normalized to 100. Dialogue/history change preference evidence, never add duplicate benefit rewards. Adaptive alpha .7/.5/.3 from profile completeness. Require clause evidence for hard cover, exclusions override headline labels. Unknown critical evidence cannot pass as suitable.
5. Rank deterministically, diversify only eligible near-equivalent families, disclose conditional underwriting and weight sensitivity. Exact score contributions and clause IDs ground why/why-not. Counterfactuals rerun the same engine.
6. Schema-bound extraction proposes updates; confirmation precedes consequential changes. A deterministic extractor remains available without an external model. Version, audit and undo confirmed state. Durable preference memory requires distinct consent; current explicit values win; support export/deletion. Research capabilities are random bearer secrets, bounded and expired, never shared across visitors.
7. Build an accessible separate `/research` workspace. Public chat remains general guidance. Chat redesign is feature flagged, lazy loaded, session-only, with safe streaming, graceful voice fallback and bounded temporary uploads. Reuse current support tickets; no chat DB migration.
8. Evaluate generated persona fixtures, filter invariants, arithmetic, evidence, precedence, privacy and browser flows. Optional learned ranking stays disabled unless held-out evidence beats baseline without violations. No fabricated model quality, clinical assurance or real-device sign-off.

Synthetic experimental exports remain physically separate from runtime visitor state. No raw public chats enter training. Real underwriting, sales, payments, signed-in intake and servicing are outside these new feature changes. Existing original-plan production blockers remain documented in `docs/uk/LAUNCH_READINESS.md`.

Phase exit checks are recorded with each implementation commit and in the final research report. Real deployment/regulated brokerage approval is outside this synthetic demo.
