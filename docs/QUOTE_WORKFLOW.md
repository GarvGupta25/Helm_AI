# Get a quote — integrated 576-plan journey

Updated 24 October 2026. The earlier separation between the public quotation journey and the recommendation workspace was incorrect for the intended product flow. The canonical entry is now `/get-cover/quote`; `/research` and `/get-cover/compare` redirect there. The old 30-plan wizard is no longer routed from the public site. Its source and legacy API remain for compatibility; no historical records were deleted.

## Current user workflow

1. **Get a quote.** Homepage/header links open the integrated comparison. No separate research page or sign-in is needed.
2. **Confirm needs.** Enter adult age, UK region, adults/children, budget, excess ceiling, hospital list and required/preferred benefits. Explicit hard limits are distinguished from preferences. Use fictional details. This synthetic family formula uses one adult age and household counts, not individually underwritten family members.
3. **Get recommendations.** The server loads the full 576-variant catalogue. An incomplete catalogue fails closed. It filters availability, essential benefit evidence, strict budget/excess and hospital requirements, calculates tax-inclusive synthetic prices and scenarios, then applies Standard/Contextual/Fusion ranking. Up to three different policy families are shortlisted. It does not display all 576 as recommendations or silently relax requirements when none qualifies.
4. **Understand and compare.** Within this same page, inspect scores/contributions, why/why-not, premiums, annual limits, exclusions, existing-condition uncertainty, clause evidence, scenario spending and the comparison table. Change needs through controls or confirmed conversation proposals; rerank or undo. What-if results are previews and cannot be selected until the changed needs are confirmed in the real comparison. Optional consented memory and export/deletion controls remain available here.
5. **Select a plan.** `Select this plan` opens a review with the server-calculated base premium, tax, monthly/annual total, excess/copay, benefit limits and key facts. Four acknowledgements start unticked. There is a back-to-recommendations action; no purchase occurs on selection.
6. **Confirm the demo.** After all acknowledgements, `Confirm demo selection (£0 collected)` validates the stored shortlist and profile version, rechecks eligibility/validity and saves a receipt inside the encrypted private session. Another visitor's session, arbitrary plans, stale profile versions and unstored what-if runs cannot be confirmed. Retries for the same selection return the same receipt; a conflicting selection for that comparison is rejected.
7. **Keep a record.** The confirmation has a demo reference and a local JSON download containing the selected quote, policy snapshot, synthetic clauses, scores, confirmed needs, scenarios and acknowledgement time. Refresh restores the confirmation while the session/profile is valid. Changing confirmed needs hides the old confirmation from the current flow; its historical record remains in session export until deletion/expiry. Default session retention is 24 hours; opt-in durable retention follows existing settings.

## What happens after confirmation today

The public flow ends at the demo confirmation. **It does not collect payment, submit an insurance application, perform real underwriting, obtain insurer acceptance or issue a policy.** It does not create/link an account, email documents, activate a policy or insert it into the signed-in customer dashboard. No claim, payment schedule or renewal is created from this synthetic selection. These facts are also stated on the confirmation screen and receipt (`paid_pence=0`, `policy_created=false`, `account_linked=false`, `email_sent=false`).

The repository has older authenticated customer policy/claims/servicing workflows, but they are a separate historical system. Selecting a synthetic plan does not connect to them automatically. Connecting issued-policy lifecycle records would be additional implementation; this integration does not imply that it is already present.

## Implementation and verification

- The existing recommendation interface is reused at the normal quotation route, retaining its explanations, comparison, what-if, memory and privacy controls.
- Capability-protected `/api/v1/quotation/confirm` and `/quotation/confirmation` persist/retrieve selection receipts. State updates are explicitly marked dirty so the initial comparison is saved before confirmation. PostgreSQL row locks serialize session operations; execution tests use SQLite, so real PostgreSQL concurrency is not certified.
- Tests exercise confirmation consent, eligibility, session isolation, stale versions, idempotency, conflicting choices, refresh/download, canonical routing and absence of calls to the legacy `/api/uk/quotes` endpoint.
- Screenshot evidence: `docs/chatbot-screenshots/quote-review.png`, `quote-confirmation.png` and the refreshed comparison screenshot. The existing original-production blockers remain documented separately.

Verification for this integration: 33 focused backend tests passed, including the new confirmation checks; all 15 public/quotation/chat browser tests and all nine existing customer browser tests passed. Frontend build/typecheck, scoped ESLint, Ruff and diff whitespace checks passed. No payment or customer-database mutation was performed.
