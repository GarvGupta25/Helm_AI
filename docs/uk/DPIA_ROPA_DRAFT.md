# DPIA and processing register — draft, not approved

Owner: DPO [TBC]. Review date 22/10/2026. Status: NOT APPROVED FOR LIVE USE.

| Processing | Data | Purpose | Retention proposal | Basis / condition |
|---|---|---|---|---|
| Quote calculation | DOB, postcode, smoking and preferences in request memory | Synthetic comparison | Request only; quote snapshot excludes DOB/full postcode | DPO must approve Article 6 basis |
| Structured health answer | Optional boolean after consent | Demonstrate consent gating | Not persisted; consent purpose/version retained | Article 9 condition requires approval; no inference transfer |
| Quote snapshot | Prices, selected benefits, needs statement, bearer capability | Demo resume and review | Seven days | Operational deletion job required |
| Public assistant | Message in memory; stored intent and timestamp only | Information / safety routing | Audit metadata 30 days proposed | No raw text or diagnosis logging |
| Demo support ticket | Reason, audit reference, generated summary | Demonstrate escalation | 30 days proposed | No live adviser delivery |
| Cookie preferences | Categories, version, timestamp on device | Respect choice | Until cleared or refreshed | Essential preference storage; optional scripts absent |
| Existing customer accounts | Historical auth and policy data | Existing account workflows | Existing schedule must be reviewed | UK migration and processor review outstanding |

Risk assessment: health inference from inputs; accidental logs; token disclosure on shared devices; overseas processing in existing services; data-subject requests without verified controller; pricing misunderstanding; human support unavailable. Mitigations implemented: no free-text health forms, no raw public-message retention, inference disabled for public guidance, bounded messages, consent gates, quote expiry, capability in header/session storage, fictional labelling, real-payment disabled, live build guard.

Required before launch: identify controller/processors/regions; data-flow mapping for all existing authenticated agents; approve Article 6/9 bases and notices; transfer mechanism and DPA review; log redaction review at reverse proxy; encryption/KMS controls; authenticated account linking; deletion scheduling with evidence; rights workflow; DPO consultation; remaining-risk acceptance and sign-off.

The word 'consent' in a table is not proof of a valid lawful basis. Demonstration consent does not authorise live insurance processing.
