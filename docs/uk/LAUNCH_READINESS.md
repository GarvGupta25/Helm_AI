# Launch readiness — NO-GO for real insurance distribution

## Guided journey update —25 October2026

Development Phases0–13 are implemented behind VITE_QUOTE_WIZARD; actual evidence is in docs/ux/WIZARD_PROGRESS.md. Insurers, prices and requests remain synthetic. Prototype completion does not constitute release sign-off.

| Gate | Next required evidence |
|---|---|
| Automated checks | Full backend/frontend and browser results, scoped axe and dependency audits recorded in the phase ledger |
| Messaging | Real Meta business/number/template approval, SMTP delivery, callbacks and cross-device recovery with configured providers; locally console only |
| Real insurers | Carrier agreements, approved products/IPIDs, authenticated adapter contract tests, underwriting and failure/reconciliation procedures |
| Broker operations | Genuine Supabase broker sign-in, administrator assignment, staffing and review SOP; authorization is API-tested |
| Storage/infrastructure | Rehearse migration0008, backup/restore, PostgreSQL races, key rotation, object-store authorization/retention, edge limits, HTTPS cookies and logging |
| Privacy | Complete controller identity, DPIA/ROPA, processor/transfer contracts, rights procedures and operational retention scheduling |
| Accessibility/research | Physical phones, manual NVDA/VoiceOver,200/400% browser zoom and real UK user sessions |
| AI/document governance | Approved insurer forms, legally reviewed checklist wording and live-provider evaluations; generated outputs still require exact human approval |
| Performance | Guided page lab measurements in docs/ux/PERFORMANCE.json; field vitals/deployed SLA unverified |
| Production guard | build:production intentionally exits1; no approval to remove it |

See docs/ux/SECURITY_PRIVACY_REVIEW.md and QA_CHECKLIST.md. Earlier baseline below retains its historical scope.

## Earlier readiness baseline

The repository contains phase checkpoints, not a completed acceptance certificate. The owner requested phasewise commits on main, and that is the branch used. No hosted deployment or real payment was performed.

| Area | Current state | Remaining work / owner |
|---|---|---|
| Source safety | Original main preserved as local/remote uae-final | Owner retains backup; no customer data modified |
| UK public experience | New shell, Home/About, content, quote demo and reviewed chat | Exact reference motion, page-complete editorial review and approved media / design owner |
| Historical transformation | Additive UK schema/rates; old records and archives retained | Active legacy contracts, agents, payment paths and professional models still need migration / engineering |
| Legal identity | Visible placeholders; no false authorisation | Real entity, FRN/principal, ICO, address, scope/remuneration / owner + compliance |
| Distribution | Fictional comparison; no advice or live sale | Approved IPIDs, product governance, advice/suitability and carrier agreements / compliance |
| Payment and resume | £0 simulation, session-token resume | Real test gateway integration, secure email magic links, account linking / engineering |
| Human support | Intent-only demo tickets | Staff dashboard, callback calendar, staffing, SLAs, language support / operations |
| Privacy | No public inference transfer or transcript retention; draft DPIA/ROPA | Historical-agent processor/transfer review, lawful bases and scheduled retention / DPO |
| Accessibility | Automated browser checks and scoped primitives | Manual NVDA/VoiceOver, 400% zoom, full WCAG audit and actual devices / accessibility owner |
| Performance | Desktop Home/About: 99/100; mobile: 83/79 | Mobile About remains below 80 and mobile LCP exceeds 2.5s; field vitals unverified / engineering |
| Consumer understanding | Research script, consent and scoring pack | 15+ real UK sessions and retesting / research owner |
| Security | Tested auth boundaries retained; reviewed public routes | Complete ASVS L2 assessment, distributed limits and deployment headers / security owner |
| Sign-off | None fabricated | Compliance + legal + DPO + business approval |

`npm --prefix frontend run build` creates a permanently labelled demonstration. `npm --prefix frontend run build:production` intentionally fails while live-release blockers and regulatory placeholders remain. A passing demo build must never be described as live-launch approval.

The historical-term inventory is in `uae_leftovers.csv`: 359 matches at final verification, including historical application/archive content and intentional guardrail inputs. The public-source guard covers only the newly built UK public modules; it is not a whole-repository clearance. Do not substitute an allow-list or deleted archive for a completed migration.

See PHASE_REPORTS.md, CHANGELOG_UK.md, evidence/, OPEN_QUESTIONS.md and the research/security/retention runbooks for evidence and outstanding acceptance items.
