# Guided quote wizard — audited contract

Audited 25 October 2026 against main 3959581. Source brief: GUIDED_JOURNEY_PLAN.md. The owner explicitly authorised continuing all phases and pushing each gate; document instructions to stop are superseded. No application code changes in Phase 0.

## Source of truth

The canonical current profile is `backend/app/journey/schemas.py:JourneyProfile`, not the older `/api/v1` research profile. Use `/api/journey`, `X-Journey-Session`, `frontend/src/journey/api.ts`. Preserve the separate older research capability unchanged. The current one-page UI is `frontend/src/journey/Intake.tsx`; public routing lives in `uk/PublicApp.tsx`.

Seven essentials are exactly people with every age or birth date, location.region, cover.start_date, budget.choice (amount needs monthly_pence), excess.choice (amount needs max_pence), hospital_list.choice (minimum_tier needs minimum_tier), benefits.required != null. Explicit [] is answered, null is unanswered. Server completeness is authoritative; start date must be today through +365 days. Confirmed versions, not autosaved drafts, drive recommendations.

## Field, routes and control contract

| Route suffix under /get-cover/quote | Tier | Canonical fields / exact choices | Validation / help meaning |
|---|---|---|---|
| root | choice | manual / chat, session UI preference | Same encrypted server draft; ~5 minutes |
| consent | optional | health_consent via /health-consent | Explicit health benefit/smoking processing; declining blocks sensitive values, not navigation; withdrawal erases sensitive history/derived cases |
| people | mandatory | people[].relationship lead_adult/partner/child; age_years or date_of_birth; smoker_status yes/no/unknown/prefer_not_to_say/null | Exactly one lead adult; max 2 adults 18–85 + 6 children 0–17; max 8 people; consistent DOB; smoking recommended, consent required |
| region | mandatory | location.region England/London/Scotland/Wales/Northern Ireland | Searchable choices; no inference from postcode |
| start-date | mandatory | cover.start_date ISO date | Today through 365 days ahead; actual age eligibility checked on start date |
| budget | mandatory choice | budget.choice amount/no_target; monthly_pence integer 0..1000000; strict boolean | No target valid; strict maximum hard only for amount |
| excess | mandatory choice | excess.choice amount/no_preference; max_pence 0/25000/50000; strict | Contribution to eligible treatment; no silent relaxation |
| hospitals | mandatory choice | hospital_list.choice minimum_tier/no_preference; minimum_tier 1/2 | Minimum tier hard, not an actual network guarantee |
| benefits/hospital | mandatory group | inpatient, diagnostics, outpatient, cancer, emergency | Values none/preferred/required map to existing arrays; unknown/excluded required cover fails |
| benefits/wellbeing | mandatory group | mental_health, physio | Same arrays, no overlap/duplicates; consent for priorities |
| benefits/everyday | mandatory explicit review | dental, maternity, chronic, pre_existing | Explicit essential-benefits review including none; existing conditions never assumed covered |
| ready | checkpoint | Seven essentials, confirm draft | Show my plans or optional details |
| optional/existing-cover | recommended | cover.existing_cover none/switching/renewing/unknown/null | Switching context only |
| optional/underwriting | recommended | cover.underwriting moratorium/full_medical/no_preference/unknown/null; underwriting_required | Hard needs an actual supported method; existing conditions not inferred covered |
| optional/outpatient | recommended | outpatient.minimum_annual_pence integer 0..10000000/null; required | Essential requires amount; optional level is a preference |
| optional/postcode | optional | location.postcode null or UK postcode regex, max12 | Does not override region |
| optional/conditions | optional | health.existing_condition_scenario yes/no/prefer_not_to_say/null | Fictional scenario, not diagnosis; consent for yes/no |
| review | review | All canonical fields, confirmed version/history/undo | Exact step edit links, no raw analytics by default |

## Copy deck

Each step heading names its topic: Before we start; Who needs cover?; Where do you live?; When should cover start?; Your monthly budget; Your maximum excess; Hospital access; Hospital and treatment; Mind and body; Everyday and life events; Your essentials are done. Optional headings retain underwriting/outpatient terminology and add a plain explanation. One helper line comes from the inventory above; Why do we ask expands that same meaning. No medical/personal advice or real network promise.

## APIs and existing reuse

GET /profile restores draft+confirmed/version/revision/hash. PATCH /intake/draft validates expected_revision; POST /profile/confirm validates exact draft hash and expected_version. Autosave does not confirm. /profile/history and /profile/undo remain. /recommendations and /runs/:id store frozen snapshots. /shortlist already accepts 0–3 plan ids. /quote-requests already accepts 1–3 with stale/idempotency/conflict/consent/contact checks. The older /api/v1/quotation/confirm remains single-plan for its legacy route; do not change it to a second journey implementation.

Current engine returns family-diverse top3 and light alternatives lacking policy details. Extend via an optional limit preserving the default3 and the identical top3; append eligible ranked variants, not replace the diversity logic. View filters must not mutate the profile.

Current /quote-dashboard uses a fragment token, deliberate interstitial, hashed grant and HttpOnly cookie exchange. Keep the fragment (safer than logging a path token); add /my-quotes alias. Cases, grants, delayed adapters, PDFs, reminders, broker role/assignment/signoff already exist and must be reused.

## Test inventory

`tests/uk/intake.spec.ts`, `broker.spec.ts`, `research-chat.spec.ts`, `public.spec.ts`, `member-feedback.spec.ts`, `scroll-composer.spec.ts`; inspect exact names before edits. Backend `test_journey*.py`, research engine and confirmation checks remain. Existing UI tests run flag-off; new wizard tests run with flag-on. Add registry, autosave races/restore, payload equality, consent and direct deep-link checks. Use existing 60 personas with an explicit mapping report, not invented equality claims.

## Decisions

D1/D2 adopt optional order and groups in source plan. D3 up to10, preserve default3 and diverse top3. D4 reuse current separate broker.html; never restore archived obsolete auth. D5 broker sharing opt-in, never automatic without consent. D6 official Cloud API interface, sandbox default; live requires credentials, approved templates and allowlist. D7 deterministic fallback always, existing Groq optional per-message consent. D8 documented >=90 excellent / >=75 strong / >=55 fair / otherwise limited, no regulated suitability claim. D9 replace side panel with checkpoint/review; retain compact live summary in chat.

English-only UI remains per earlier explicit owner request; structural RTL may be tested without restoring Arabic controls. No actual current quote dark-mode variant exists: capture this gap rather than claim preservation. New scoped dark styling may reuse existing navy tokens. Current wizard flag defaults off until final reviewed demo build; legacy route stays reachable. No live insurer/payment, no fabricated provider success, production guard stays closed.

## Gates and limits

Every phase records commands, actual results and unverified items in WIZARD_PROGRESS.md, commits as Utkarsh Raj, fetches/integrates and pushes. Physical devices, screen readers, WhatsApp onboarding, live provider delivery and PostgreSQL concurrency remain external verification. Any unavailable external capability stays explicitly unavailable; continue independent prototype work.
