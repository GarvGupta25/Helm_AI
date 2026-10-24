# Journey development ledger

The owner authorized continuous phasewise implementation without repeated phase approvals. All integrations remain simulated; human approval of AI-authored outgoing artifacts remains mandatory. Commit author: Utkarsh Raj.

## Phase 1 — shared intake

Delivered isolated encrypted draft sessions, explicit missing fields, a canonical typed profile, consent-protected health preferences, immutable confirmed versions, stale-write rejection, undo, deterministic reviewed-field extraction, lossless manual/guided modes, missing-field recovery, and narrow-screen/RTL guided questions. Existing research remains available at `/get-cover/legacy-demo`; the normal quote entry is the new intake.

Checks: canonical schema/intake API tests, TypeScript/build, manual-to-chat persistence browser flow, scoped axe and narrow RTL layout. Exact final counts are recorded in the final verification section when the complete journey is checked.

Limits: no live LLM calls, no diagnoses, no real submissions; extraction supports the documented controlled question vocabulary. Birth dates are optional alternatives to ages. The new recommendation adapter is Phase 2.

## Phase 2 — recommendations and exploration

Delivered deterministic per-adult rating with explicit fictional child/family terms, version-qualified frozen plan snapshots, effective-date/underwriting/outpatient hard filters, unchanged reference weights, no-target budget neutrality, current-run ownership, persistent shortlist/remove, three-plan price/limit comparison, saved-run restoration, profile history, and nonselectable what-if previews.

Checks: 24 schema/intake/recommendation/existing-engine tests passed, the comparison ownership/preview API test passed, scoped ESLint and build passed, and all three intake/comparison/RTL browser tests passed. A browser check caught delayed checkbox feedback; selection now responds immediately and rolls back on server rejection.

Implementation choice: immutable version-qualified family facts are frozen in encrypted run/quotation snapshots rather than overwriting existing research catalogue records or adding a duplicate catalogue database. Single-adult arithmetic is covered by compatibility vectors. Family terms remain invented demo assumptions, not underwriting evidence.

## Phase 3 — policy-specific questions

Delivered plan/run-owned fact retrieval, cited premium/benefit/exclusion/underwriting/network answers, deterministic fixed-scenario calculations, unknown/refusal paths, and private saved broker questions. The UI keeps at most 20 escaped plain-text turns per plan/run in browser-tab storage, supports clearing, shows source fields/versions, and restores focus when closed.

The versioned evaluation corpus contains 50 questions: 40 supported fact/scenario questions and 10 unknown/adversarial questions, each checked against three different synthetic policies. No external provider writes customer-facing prose; answers use controlled templates. Broker questions are saved, not delivered without later sharing consent and assignment.

Checks: all 51 policy tests, TypeScript and scoped ESLint passed. The later real-API browser flow also exercised a policy premium answer and focus return.

## Phase 4 — verified demo requests

Delivered fake contact verification with keyed OTP digests, expiry/attempt limits, protected inboxes and replay rejection; explicit versioned insurer/broker/channel consent; up-to-three plan review; optional dual contact channels; quiet-hour preferences; private seven-day case snapshots; grouped per-insurer idempotent requests; deterministic delayed insurer simulation; bounded timeout retries; partial-response support; immutable synthetic quotation documents.

Checks: contact/request/worker tests all passed (3 focused tests), including contact ownership boundaries, consent withdrawal, duplicate requests, timeout retry and duplicate worker runs. Build, TypeScript and lint passed. All three intake/browser flows passed, including policy questions, fake OTP capture/verification and creation of a consented request.

The worker runner explicitly selects the scratch database/key and cannot send externally. Consent/audit/message collections are bounded encrypted case/session records rather than extra relational tables; this avoids a second identity system while preserving typed API contracts. Relational case/request/document/approval/grant/job tables enforce the critical boundaries. Account linking to legacy customer records remains intentionally absent.
