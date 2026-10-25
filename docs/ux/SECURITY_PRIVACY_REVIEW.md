# Guided prototype security and privacy review

25 October2026. Scope: new guided journey and connected broker/dashboard controls. Synthetic local test data only. This is an engineering review, not legal, regulatory or penetration-test certification.

## Security evidence and practical limits

- Capability ownership, stale version/revision,1–3 selection, exact consent, role/assignment, cross-case isolation and approval gates are covered by API tests. The full suite result and final browser results are in WIZARD_PROGRESS.md.
- OTP: international normalization, six CSPRNG digits, keyed salted digest,10-minute lifetime, five committed guesses, replacement/consumption and timing-safe check. Encrypted rolling number/session windows enforce3 sends/hour and60s cooldown; existing10/IP/hour limiter stays unchanged. New-flow contacts cannot use the old demo verifier. Legacy early-broker verification intentionally remains a private **simulation**, not real ownership proof. Console codes exist briefly in bounded memory; do not log or screenshot them.
- Link:256-bit random token stored by digest; fragment delivery avoids HTTP path/query logs. Deliberate interstitial exchange, single use,24/48h expiry, parent-bound cookie max2h, HttpOnly+SameSite=Strict and Secure in production configuration. no-store/no-referrer headers remain. Renewal needs original-contact OTP; old grants/sessions revoke.
- Mutations of access, new verification, privacy and optional counts enforce origin/cross-site checks. Capability APIs require the secret header; role APIs require authenticated bearer plus assignment. Tests cover hostile origins, absent/wrong capabilities, expired/withdrawn access and unauthorized PDF/export.
- Broker drafts record sources/input/output hashes/method and prompt version. Rejection notes and approved checklist/time/actor are audited. Editing or changing scope invalidates approval. AI cannot sign off. Exports need the assigned approving human and an exact live approval. Human-authored message functionality remains separate from generated drafts; no automated external submission exists.
- User text renders as React text. New provider output is schema-constrained and fails back to deterministic content. No LLM arithmetic or eligibility decision. The broker evaluation measures controlled templates, not unrestricted model accuracy.
- Dependencies: initial Python audit reported42 advisories across4 packages. Updated certifi, Pillow13, urllib3 and langgraph-checkpoint-postgres (plus required checkpoint dependency). Final pip-audit and both npm audits report zero known advisories. See DEPENDENCY_AUDIT.json for pinned versions/counts. This is point-in-time tooling, not proof of absence of vulnerabilities.
- High-confidence secret-pattern scan covers changed text; no private key/access-token matches reported. It does not certify historical Git objects or server secrets. Environment files, keys, local databases and raw traces/logs remain ignored.
- Remaining: production database row-lock races, distributed/edge limits, CDN/cache/log configuration, operational key rotation, provider webhooks, a formal security review and hostile deployed-browser assessment. Application in-memory limits reset on restart and do not provide multi-instance protection. Production guard stays closed.

## Data map and retention

| Data | Store / access | Lifetime / removal |
|---|---|---|
| Draft/confirmed profile, history, proposal, plans | Encrypted JourneySession/ProfileVersion/JourneyRun; capability owner |24h default; expired access blocked and retention purges contents; visitor deletion removes rows |
| Contact destination/OTP metadata | Encrypted Contact; keyed lookup/code hashes | OTP10min; contacts within7d, consumed code invalid; visitor deletion removes contacts and volatile codes |
| OTP abuse window | Encrypted OtpWindow keyed by HMAC | Hour-window cleanup; visitor deletion removes its session bucket; shared number bucket expires normally to preserve abuse protection |
| Cases/profile snapshot/notes/messages/approvals/docs | Encrypted case/document/job payloads, assigned consented broker or private dashboard | Up to7d; derived grants/docs/jobs deleted with case. Approval metadata keeps actor/hash/time during case lifetime; no permanent audit guarantee |
| Private grants | Token digest, encrypted local delivery inbox; contact-bound dashboard cookie |24/48h links, max2h dashboard; revoke on renewal/withdrawal/visitor deletion |
| Funnel | UTC day + fixed event/step/mode/choice counts only |30d rolling; disabled unless operator flags and visitor Analytics consent; no visitor join/delete key |
| Chatbot feedback | Separate feedback database, random tab/response reference and user-submitted feedback |90d, optional answer sharing; no account link; not part of journey deletion |
| Local member accounts | Separate encrypted local account records and salted password hash | Separate service lifecycle; not affected by journey deletion. Historical customer/Supabase accounts remain separate |
| Rate limiter / server logs | Ephemeral IP buckets, local service access logs | Limiter1h; counts table has no IP. Operational log retention/redaction needs deployment approval |

Visitor controls in the wizard: export saved current/history/comparison data and contacts/cases (excluding capabilities, grants and OTP material), or explicitly delete the journey and its derived state. Server tests verify another session survives. Health-consent withdrawal separately removes sensitive preference/smoking history and derived cases. Delete/export using the same private tab; capability loss cannot be recovered as an authenticated identity. Private downloads may contain submitted details: store securely. Anonymous aggregate counts cannot be identified or selectively erased because no visitor key exists.

## Processors and wording

Local prototype: application/API+SQLite, self-hosted fonts/assets and browser features. No Groq call or WhatsApp/email network send was exercised. When explicitly configured: Groq receives validated current-question text/profile context or approved narration sentences only after per-message permission; official WhatsApp receives normalized contact and approved authentication/utility template data; SMTP receives approved email destination/content; Supabase supplies separate professional authentication. Hosting, backup, SMTP, Meta/Groq/Supabase contracts, subprocessors, transfers, lawful bases, DPIA and rights procedures require DPO/legal approval before a real pilot. No compliance or FCA-authorisation claim.

Consent versions: health-demo-v1; journey-sharing-v1 for named insurer/broker/notification scope; verification-only permission recorded with the new-flow challenge; cookie-choice version1 for optional counts; per-message provider consent is not reusable marketing/health permission. Regulatory checklist demo-review-v1 is editable prototype content pending legal review. No production template, insurer agreement or sign-off is fabricated.
