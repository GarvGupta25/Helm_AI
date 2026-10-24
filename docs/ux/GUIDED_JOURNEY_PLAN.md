# plan.md — Helm AI Guided Quote Journey

> Scope: redesign the quote experience of Helm AI (UK private medical cover demo) into an Oscar-style, one-step-at-a-time journey, then extend it through plan comparison, WhatsApp-verified access, a private magic-link dashboard, and the broker workflow.
> Baseline: `PROJECT_OVERVIEW.md` (commit `5e8596d`, 24 October 2026) plus the screenshots of the current one-page quote form and the Oscar reference flow.
> Status: **planning document. No phase starts until the previous gate is approved.**

---

## 0. How to use this document

1. Give your coding agent **Section 1 (invariants) + Section 4 (UX rules) + one phase's master prompt** at a time. Never hand it the whole file as a single task.
2. Every phase ends at a **gate**: the agent reports what changed, which checks actually ran and their real results, what was *not* verified, and open decisions. You approve before the next phase.
3. Before any work: read `AGENTS.md`, `docs/QUOTE_WORKFLOW.md`, `docs/research/README.md`, `archive/README.md`; run `git status`, `git fetch`, `git pull --ff-only`. The repository is `GarvGupta25/Helm_AI` (not `Insurance_UAE`). Never force-push, never overwrite a collaborator's work.
4. Update `PROJECT_OVERVIEW.md`, `docs/QUOTE_WORKFLOW.md` and `AGENTS.md` whenever behaviour, routes or setup change.

---

## 1. Goals and invariants

### 1.1 What is wrong today (from the current-page screenshot)

The whole intake is **one very long page**: mode toggle, consent, people, region, postcode, start date, existing cover, underwriting, budget, excess, hospital list, outpatient minimum, eleven benefit dropdowns, an existing-condition scenario, a broker button and the submit action, with a "Your shared profile" panel beside it. Nearly every input is a dropdown. Results explain themselves with raw point scores ("coverage 24.63 points", "alpha 0.3") and a flat list of caps and exclusions. It is accurate but heavy.

### 1.2 What we are building

- A **guided wizard**: one topic per screen, a stage progress bar, Back/Next, auto-save, simple controls (chips, steppers, yes/no, short fields).
- A **first-screen choice**: *Fill it in myself* or *Let the AI ask me*. Both fill the **same** profile and can be switched at any time.
- **Mandatory questions first.** When the optional questions begin, **Show my plans** becomes visible and stays visible.
- **Separate pages** for plans, plan details, comparison, selection, verification, link choice and dashboard.
- **Plain-English, textual explanations** instead of numeric/analytic breakdowns (numbers remain available behind a "show the numbers" disclosure).
- **Left-hand filter sidebar** on the plans page, like Oscar.
- After selecting up to **3 plans**: WhatsApp number → **real WhatsApp one-time password** → choose **24 h or 48 h** magic link → **private dashboard** with all quotations, breakdowns, downloads, comparison and an LLM assistant.
- **Contact a broker** available at any point; cases reach a **Broker Workspace** with an AI assistant and human sign-off.

### 1.3 Invariants — do NOT change

| Area | Rule |
| --- | --- |
| Look and feel | Keep the existing colours, fonts, spacing/radius/shadow tokens, header, footer, button styles and tone. Read them from the existing token/CSS system (`frontend/src/ui/`, `frontend/src/uk/`); never guess hex values or add a new design library. |
| Questions | Keep every existing question, its field key, option values, validation rules, help text meaning and FCA-oriented wording. Only **presentation, order and control type** change. |
| Semantics | Keep hard requirement vs soft preference, "unknown or excluded required cover fails the requirement", "never silently relax hard limits", and "existing conditions are never assumed covered". |
| Engine | Ranking, pricing and eligibility stay **deterministic and server-side**. The LLM never sets a price, score or eligibility. |
| State | Keep versioned profiles, undo, the private encrypted research session, and the `X-Research-Session` capability (a secret: never in logs, URLs, screenshots or commits). |
| Boundaries | Insurers, plans and prices stay **synthetic**. No payments. No claim of FCA authorisation or regulated advice. Keep the "demo — not a real insurance service" disclosure on every page. |
| Safety rails | Keep the production guard failing, keep the request limiter, keep secrets out of `VITE_*` and out of Git. |
| Human in the loop | Anything AI-drafted that reaches a customer, insurer or regulator-facing document needs recorded human approval. |

---

## 2. Reference analysis: Oscar vs Helm today vs Helm target

Oscar's shop (`oscar.stridehealth.com/shop/location`) was reviewed from the supplied screenshots; the live URL only exposes the first step shell (progress labels *Location → Coverage → Savings → Personalize*), so deeper behaviour below comes from the screenshots.

| Aspect | Oscar | Helm today | Helm target |
| --- | --- | --- | --- |
| Structure | 4-stage progress bar, one decision per screen | One long page + side summary | 4-stage progress bar, one decision per screen |
| First question | ZIP code, single field, one big button | Mode toggle + consent + 14 fields visible | Mode choice, then one question at a time |
| People | Card per person, DOB/sex/flags, "Add spouse / Add dependent" | "Add adult / Add child" buttons | Same idea: one card per person, simple fields |
| Next button | Disabled until the step is valid | Single submit at the bottom | Disabled until valid, with inline reasons |
| Results | Filter sidebar + sortable cards + Compare checkbox + Details + Enroll | Shortlist of ≤3 with score panels | Sidebar + ranked cards + Compare + Details + Select |
| Detail page | "Why is this plan the best?" in words, "See how we estimate" | Point scores, caps list | Plain-English sections, numbers behind a disclosure |
| Tone | Short labels, helper line under each field | Dense hints on every field | One helper line, "Why do we ask?" on tap |

**Progress-bar mapping** (Oscar's *Savings* has no UK equivalent):

| Oscar | Helm |
| --- | --- |
| Location | **About you** (who, where, when) |
| Coverage | **Your cover** (budget, excess, hospital, benefits) |
| Savings | **Fine-tune** (optional questions) |
| Personalize | **Your plans** (results, details, compare, select) |

After *Your plans*, a second lightweight tracker covers **Verify → Your link → Your quotes**.

---

## 3. Target journey and routes

| # | Screen | Route (proposed) | Primary action |
| --- | --- | --- | --- |
| 0 | Mode choice | `/get-cover/quote` | Fill it in myself / Let the AI ask me |
| 1 | Before we start (consent) | `/get-cover/quote/consent` | Agree and continue |
| 2 | Who needs cover | `/get-cover/quote/people` | Next |
| 3 | Where | `/get-cover/quote/region` | Next |
| 4 | When | `/get-cover/quote/start-date` | Next |
| 5 | Monthly budget | `/get-cover/quote/budget` | Next |
| 6 | Excess | `/get-cover/quote/excess` | Next |
| 7 | Hospital list | `/get-cover/quote/hospitals` | Next |
| 8a–c | Benefits (3 grouped screens) | `/get-cover/quote/benefits/:group` | Next |
| 9 | **Essentials done checkpoint** | `/get-cover/quote/ready` | **Show my plans** / Add optional details |
| 10a–e | Optional fine-tune | `/get-cover/quote/optional/:topic` | Next / Skip — **Show my plans always visible** |
| 11 | Check your answers | `/get-cover/quote/review` | Show my plans |
| 12 | Plans | `/get-cover/plans` | Details / Compare / Select |
| 13 | Plan detail | `/get-cover/plans/:planId` | Select / Ask about this plan |
| 14 | Compare | `/get-cover/compare` | Select up to 3 |
| 15 | Review selection | `/get-cover/selection` | Continue |
| 16 | WhatsApp number | `/get-cover/verify` | Send code |
| 17 | Enter code | `/get-cover/verify/code` | Verify |
| 18 | Link validity | `/get-cover/access` | 24 hours / 48 hours |
| 19 | Private dashboard | `/my-quotes/:token` → `/my-quotes` | View, compare, download, ask |
| 20 | Broker contact | floating action on every page | Talk to a broker |

Note: `/get-cover/compare` and `/research` currently redirect to `/get-cover/quote`; the compare redirect must be replaced and documented.

---

## 4. UX rules (apply to every phase)

1. **One topic per screen.** A group of closely related tiny fields (for example date of birth + sex for one person) may share a screen.
2. **Controls, not dropdowns.** Use the control that makes the answer fastest:
   - Numbers → stepper or numeric field with units shown.
   - Yes/No → two large buttons (not a checkbox).
   - Small fixed sets (≤5 options) → chips or segmented buttons.
   - Long sets (region) → searchable list.
   - Dates → one date field with quick chips.
   - **Reuse the existing option values exactly**; only the presentation changes.
3. **Progress**: stage bar at top, "Step 3 of 8" for screen-reader and visual users, and a short time estimate on the first screen.
4. **Next is disabled until valid**, with the reason in text next to the button (not just a greyed button).
5. **Auto-save every answer** into the profile draft. Refresh or Back never loses data. "Save and finish later" stays available.
6. **Language**: short labels at roughly a 12-year-old reading level; one helper line; "Why do we ask?" opens a one-paragraph explanation. Keep the FCA-related wording where it carries meaning (for example underwriting) and add a plain explanation beside it.
7. **Hard vs preferred** is a single clear toggle on the same screen ("This is a must" / "Nice to have"), never hidden in a separate checkbox.
8. **Optional is labelled** "Optional" and has a visible **Skip**. Skipped means "not answered", never "no".
9. **Always-available**: Back, "Talk to a broker", language, and the demo disclosure. The AI-chat launcher is hidden inside the AI-assisted mode to avoid two chats competing.
10. **Accessibility**: focus moves to the new step heading; progress is announced; every control is keyboard operable; visible focus; 44 px targets; reduced-motion respected; RTL (Arabic) and dark mode preserved; 16 px minimum input text on mobile.
11. **Mobile first**: Next/Back sit in a sticky bottom bar; safe-area insets respected; filters become a bottom sheet.
12. **Explanations are text first.** Numbers appear only as supporting detail ("Show the numbers").
13. **Errors are kind and specific** ("Please choose a region so we can check which plans are available there").
14. **Feature flag**: the new journey ships behind `VITE_QUOTE_WIZARD`; the existing page remains the fallback until sign-off.

---

## 5. Question inventory and step mapping

Derived from the current-page screenshot. **Phase 0 must verify each row against the code and API validation** (tiers below are the screenshot's own labels).

| Existing field | Current label (tier) | New step | New control | Notes |
| --- | --- | --- | --- | --- |
| Health-related consent | Checkbox at top (optional) | Step 1 | Large agree button + "No thanks" path | Keep exact current semantics of what is blocked without consent |
| People covered | Who needs cover? (**mandatory**) | Step 2 | Person cards: age/DOB fields + Add adult / Add child | One card per person; fictional ages |
| Region | Region (**mandatory**) | Step 3 | Searchable list | Postcode never silently infers region |
| Cover start date | Cover start date (**mandatory**), today → +365 days | Step 4 | Chips "As soon as possible" + date picker | Enforce the existing validity window |
| Monthly budget | Monthly budget (**mandatory choice**) | Step 5 | Chips/slider + "No target" + "This is my strict maximum" toggle | "No target" is a valid answer |
| Maximum excess | Maximum excess (**mandatory choice**) | Step 6 | Chips + "Excess is a hard ceiling" toggle | Never silently relaxed |
| Hospital list | Hospital list (**mandatory choice**) | Step 7 | Chips with one-line descriptions | A minimum tier is an access requirement, not a real-network guarantee |
| Benefit priorities (11) | Benefit priorities (**mandatory choice**) | Step 8a–c | 3-state selector per benefit using the existing option values | Includes "I have reviewed my essential benefits, including none"; see 5.1 |
| Existing cover | Existing cover (recommended) | Optional 1 | Chips | Gives switching context only |
| Underwriting preference | Underwriting preference (recommended) | Optional 2 | Chips + "This method is a must" toggle | Existing conditions never assumed covered |
| Outpatient minimum | Outpatient annual minimum in pounds (recommended) | Optional 3 | Stepper in £ + "Essential" toggle | |
| Postcode | Postcode (optional) | Optional 4 | Short text field | Optional precision only |
| Existing-condition scenario | Existing-condition scenario (optional) | Optional 5 | Chips | Fictional scenario only, never a diagnosis |

**The seven essentials** shown in the side panel today (people, region, start date, must-have benefits, budget, excess, hospital list) become the checkpoint condition at Step 9. Phase 0 confirms the exact backend rule for "essentials confirmed".

### 5.1 Benefit screens (proposed grouping — confirm in Phase 0)

| Screen | Benefits |
| --- | --- |
| Hospital & treatment | inpatient, diagnostics, outpatient, cancer, emergency |
| Mind & body | mental health, physio |
| Everyday & life events | dental, maternity, chronic, pre existing |

Each row shows the benefit name, one plain-English line ("Stays in hospital, including surgery"), and a 3-way control mapped to the existing values (today's default is "No preference"). The last screen has a clear **"None of these are essential"** button so the review confirmation is always an explicit act. For *chronic* and *pre existing*, keep the existing caution that unknown or excluded cover cannot be treated as established cover.

---

## 6. Phases

Legend per phase: **Goal → Build → Master prompt → Acceptance → Tests → Gate**. Master prompts are written to be pasted to a coding agent *after* the invariants (Section 1.3) and UX rules (Section 4).

---

### Phase 0 — Audit, design capture and contracts (read-only)

**Goal.** Know exactly what exists and lock the contracts before any UI work.

**Build (documents only).**
- `docs/ux/WIZARD_SPEC.md`: final step table, routes, field-to-API mapping, tier per field, validation, copy deck (labels, helper lines, "Why do we ask?").
- `docs/ux/DESIGN_TOKENS_CAPTURED.md`: tokens actually used by the current quote page (colours, fonts, sizes, radii, shadows, button/chip/input styles, dark-mode and RTL variants).
- Baseline screenshots of the current quote page (desktop + 375 px, light + dark, LTR + RTL) for visual comparison.
- Decision log for the open decisions in Section 8.

**Master prompt.**

```text
You are auditing the Helm AI repository (GarvGupta25/Helm_AI) before a UX overhaul of the quote journey. Do NOT write application code in this phase.

1. Read AGENTS.md, PROJECT_OVERVIEW.md, docs/QUOTE_WORKFLOW.md, docs/research/README.md, docs/chatbot-design-notes.md, archive/README.md. Run git status/fetch/pull --ff-only.
2. Locate the current quote page implementation (frontend/src/uk/, route /get-cover/quote) and list every field: its key, label, tier (mandatory/recommended/optional), option values, validation, hard-requirement flags, and the API payload it maps to (/api/v1/profile/*, /api/v1/recommendations, /api/v1/conversation/message).
3. Determine the exact backend rule for "essentials confirmed" (the "0 of 7 essentials" panel) and which fields are required for /api/v1/recommendations to run. Record any field the UI shows as mandatory that the backend does not require, or vice versa.
4. Capture the design tokens the quote page really uses (read the CSS/token files; do not guess). Record fonts, scale, colours (with token names), radii, shadows, button/chip/input/focus styles, dark-mode and RTL variants.
5. List every existing test (tests/uk, tests/e2e, frontend unit tests) that targets the one-page quote form or the shortlist/confirmation UI and will need updating.
6. Check how selection/confirmation works today (/api/v1/quotation/confirm): it validates one selected plan per comparison. Document what must change to allow up to 3 selected plans.
7. Check how many plans the recommendations API returns and whether a ranked list longer than 3 can be produced without breaking the diversity rule for the top 3. Document options.
8. Take baseline screenshots (desktop + 375px, light/dark, LTR/RTL).
9. Write docs/ux/WIZARD_SPEC.md and docs/ux/DESIGN_TOKENS_CAPTURED.md and a decision log. List open questions for me.

Output: the documents, a summary of risks, and a request for my approval. Stop.
```

**Acceptance.** Every field in Section 5 is verified or corrected; tokens are documented from code; open decisions listed.
**Gate.** Approve the spec before Phase 1.

---

### Phase 1 — Wizard shell, routing, state and mode choice

**Goal.** A reusable guided-flow framework with the mode chooser, with no question redesign yet.

**Build.**
- `WizardLayout`: shared Helm header/footer, stage progress bar, step title area, sticky action bar (Back / Next), "Talk to a broker" link, demo disclosure.
- Step registry (data-driven): `id`, `stage`, `tier`, `fieldKeys`, `route`, `isComplete(profile)`, `canSkip`, `next/prev` rules, component.
- URL-driven steps with deep links and refresh restore; guards that redirect to the first incomplete mandatory step.
- Draft-autosave hook using the existing versioned-profile endpoints (debounced), optimistic UI, offline/429 handling.
- Mode chooser screen: **Fill it in myself** / **Let the AI ask me**; mode stored in the session and switchable from every step.
- Feature flag `VITE_QUOTE_WIZARD`; legacy page remains reachable when off.

**Master prompt.**

```text
Build the guided quote wizard shell for Helm AI. Follow Section 1.3 invariants and Section 4 UX rules of plan.md and the spec in docs/ux/WIZARD_SPEC.md.

Requirements:
- Create WizardLayout reusing the existing header, footer, tokens and button styles. Add a 4-stage progress bar (About you, Your cover, Fine-tune, Your plans) in the same visual language as the site; announce progress to screen readers; show "Step X of Y" within the stage.
- Create a data-driven step registry; no step logic hard-coded in the layout. Each step declares its fields, tier, validation (reusing the existing Zod/server rules), skippability and completion predicate.
- Routes are per step (see Section 3). Direct navigation to a later step redirects to the first incomplete mandatory step. Refresh restores the current step and answers.
- Auto-save every answer to the profile draft through the existing versioned-profile API (debounced, with retry and clear failure state). Do not create a parallel store.
- Sticky action bar: Back, Next (disabled until valid, with a text reason beside it), and on optional steps Skip.
- Build the mode chooser as the first screen: two large cards, "Fill it in myself" and "Let the AI ask me", each with a one-line explanation. Choosing either creates/uses the same research session and profile. A "Switch mode" control exists on every step; switching never loses data. In this phase the AI card routes to a placeholder that explains it is coming and offers the manual path.
- Gate everything with VITE_QUOTE_WIZARD. When off, the current one-page form stays unchanged.
- Move focus to the step heading on navigation; respect prefers-reduced-motion; keep RTL and dark mode working.
- Add unit tests for the registry and guards and Playwright tests for navigation, refresh restore, back/forward, and flag-off behaviour. Do not weaken the request limiter.

Report: files changed, tests run with real results, anything unverified. Stop for approval.
```

**Acceptance.** Deep link + refresh restore works; flag-off preserves today's page; mode switch preserves state; keyboard and screen-reader pass for navigation.
**Tests.** Registry unit tests, guard tests, Playwright navigation/restore, axe on the shell.
**Gate.** Review shell on desktop and 375 px.

---

### Phase 2 — Manual intake: mandatory steps

**Goal.** Steps 1–8 and the checkpoint, Oscar-simple.

**Build.** One screen per row of the Section 5 table for Steps 1–8c, with the new controls, helper lines and "Why do we ask?" text; person cards for Step 2; hard/preferred toggles inline; the **checkpoint screen** (Step 9).

**Master prompt.**

```text
Implement the mandatory intake steps (Steps 1–8c) and the checkpoint (Step 9) using the Phase 1 wizard shell. Use docs/ux/WIZARD_SPEC.md as the source of truth for fields, copy and validation.

Rules:
- Keep every existing field key, option value and validation. Change only presentation, order and control type. Do not add, remove or reword questions in a way that changes their meaning; plain-English helper lines are additions, not replacements of FCA-oriented terms.
- Step 1 consent: preserve the exact existing consent semantics (what is processed, what is blocked without it, withdrawal). Present it as a short screen with a clear Agree button and a "Continue without" path if the current behaviour allows it.
- Step 2 people: one card per person (like the Oscar "Myself / Add Spouse / Add Dependent" pattern but using Helm's "Add adult / Add child"), each with the age/DOB inputs the backend currently needs, remove button, max people per existing rules.
- Step 3 region: searchable list. Step 4 start date: "As soon as possible" chip + date picker limited to the existing validity window.
- Steps 5–7: budget, excess, hospital list as chips/slider; each hard-limit option is a visible toggle on the same screen ("This is my strict maximum"). "No target" must remain a valid budget answer.
- Steps 8a–c: benefits in three groups with a 3-way control mapped to the existing values; the last screen has an explicit "None of these are essential" button; completing it sets the existing "essential benefits reviewed" confirmation.
- Step 9 checkpoint ("Your essentials are done"): appears only when all seven essentials are confirmed. Primary button "Show my plans", secondary "Answer a few optional questions to sharpen your results". Show a one-paragraph plain summary of what we understood with edit links.
- Inline, specific validation messages; Next disabled until valid with the reason beside it.
- Add Playwright tests for the full mandatory path on desktop and 375 px, keyboard-only path, RTL, and dark mode. Add a contract test proving the wizard produces a profile payload identical to the legacy form for the same answers (use the 60 evaluation personas where they map to these fields).

Report real results. Stop for approval.
```

**Acceptance.** Same answers ⇒ identical profile payload as the legacy form; checkpoint appears only when essentials are complete; all hard toggles work.
**Gate.** Walk-through with you on a phone-sized viewport.

---

### Phase 3 — Optional steps, review and early "Show my plans"

**Goal.** Optional questions that never block, plus an always-visible way to get plans.

**Build.**
- Optional screens 10a–e with a visible **Optional** label and **Skip**.
- A persistent **Show my plans** control from the checkpoint onward (top-right on desktop, sticky bar on mobile), enabled whenever the seven essentials are confirmed, with a one-line note that optional answers can be added later.
- **Check your answers** page: grouped summary, edit links back to the exact step, profile version, undo, and the existing profile history disclosure.
- Skipped ≠ answered: the profile distinguishes *not answered* from *no*.

**Master prompt.**

```text
Add the optional steps, review page and early recommendation access to the Helm AI wizard.

- Optional screens in this order (confirm in the spec): existing cover, underwriting preference (+ "this method is a must" toggle), outpatient minimum in pounds (+ "essential" toggle), postcode, existing-condition scenario. Each shows "Optional", a one-line helper, a "Why do we ask?" paragraph and a Skip button. The existing-condition scenario stays a fictional scenario only; never request a diagnosis or medical document.
- From the checkpoint onward, show a persistent "Show my plans" control that is enabled exactly when the seven essentials are confirmed. Clicking it must never require an optional answer. If essentials become incomplete after an edit, disable it and say which essential is missing.
- Build the Check-your-answers page: grouped summary (People, Where and when, Budget and excess, Hospital list, Benefits, Optional details), each group with an Edit link that returns to the right step and comes back. Show profile version, Undo for the last confirmed change, and the confirmed-profile history in a disclosure. "Save draft" behaviour from the current page is preserved.
- Skipped optional questions are stored as not-answered and must not influence ranking as if the user said "no".
- Tests: skipping every optional step still yields recommendations; adding optional answers later reruns the engine and creates a new profile version; Undo works; Playwright desktop + 375 px; axe checks.

Report real results. Stop for approval.
```

**Acceptance.** User can reach plans from the first optional screen without answering any optional field; edits re-run the engine; versioning and undo intact.

---

### Phase 4 — AI-assisted intake ("Let the AI ask me")

**Goal.** The same questions, asked conversationally, answered with taps, numbers, yes/no or short text.

**Design principle.** The **server owns the question order** (the same step registry). The LLM only (a) phrases the current question simply, (b) turns the user's reply into a structured value, and (c) answers short clarifying questions from approved glossary content. It cannot invent questions, skip mandatory ones, or set outcomes.

**Build.**
- Chat-style intake UI in the Helm look: assistant bubble with the question + **quick-reply chips** for fixed options, a numeric stepper for numbers, **Yes/No** buttons, and free text allowed.
- `POST /api/v1/intake/turn` → `{assistantMessage, currentQuestion{fieldKey, tier, control, quickReplies}, proposedChanges[], summary, canShowPlans}`.
- **Direct taps and exact numbers apply immediately** (visible in a live summary with Undo); **ambiguous free text becomes a proposal card** with Confirm/Edit, as in the existing conversation flow.
- Provider abstraction: `IntakeLLM` with the existing Groq integration, a pluggable alternative provider, and the **deterministic extractor as the always-available fallback**. Per-message consent before any provider call.
- Optional questions are flagged in the chat ("This one is optional — skip any time") and **Show my plans** appears at the same point as in manual mode.
- **Switch to the form** at any time; the current question and all answers carry over.

**Master prompt.**

```text
Implement the AI-assisted intake mode for Helm AI. It must fill the SAME profile as the manual wizard through the SAME validated endpoints and step registry.

Architecture:
- Add POST /api/v1/intake/turn. Input: session capability, either a quick-reply value or free text. The server (not the LLM) decides which question is current from the step registry, validates all values with the existing schema, and returns the next question, any proposed changes, a live profile summary and canShowPlans.
- Define an IntakeLLM interface with: phrase_question(question_spec) and parse_answer(question_spec, user_text) -> JSON validated against a strict Pydantic schema, and answer_clarification(topic) restricted to approved glossary snippets. Implementations: GroqIntakeLLM (reuse existing config/consent), a second pluggable provider stub, and DeterministicIntake (templated wording + option matching + number/yes-no parsing) which is the fallback on any failure, timeout or missing consent.
- Treat all user text as data (prompt-injection safe). The LLM output can only populate fields of the current question spec; reject anything else. It can never set prices, scores, eligibility or consent.
- Direct inputs (chip tap, stepper number, yes/no button) are applied immediately with Undo. Free-text interpretations are shown as a proposal with Confirm/Edit before applying.
- Questions are asked in the registry order, one at a time, mandatory first. Mark optional questions clearly and offer Skip. When the seven essentials are confirmed, show "Show my plans" and keep it visible; do not block on optional questions.
- UI: reuse Helm chat styling; quick-reply chips, numeric stepper, Yes/No buttons, free text box (2,000 char cap), live "What we understand" summary, Switch to form, Stop, Retry, offline and rate-limit states, RTL/dark mode, session-only transcript.
- Safety: no medical advice; never ask for diagnoses or documents; the existing-condition question stays a fictional scenario; remind that existing conditions are never assumed covered.
- Privacy: per-message consent before any external provider call; no PII in logs; bounded history.
- Evaluation: write a script that replays the 60 evaluation personas through the chat intake (simulated user replies) and compares the resulting profile to the form-filled profile. Report field-level agreement, average number of turns, and fallback rate. Target >= 95% field-level agreement before sign-off; report the actual figure.
- Tests: unit tests for parsers and schema rejection, provider-failure fallback, prompt-injection attempts, mode switching mid-flow, and Playwright for a full AI-assisted run (with the deterministic provider) on desktop and 375px.

Report real results and anything not verified (live provider calls). Stop for approval.
```

**Acceptance.** Chat and form produce identical profiles for identical answers; LLM outage degrades gracefully; mode switch preserves state.

---

### Phase 5 — Plans page (Oscar-style list with filter sidebar)

**Goal.** A separate, calm results page.

**Build.**
- `/get-cover/plans`: summary strip ("2 adults · North West · from 1 Dec" with **Edit**), **left filter sidebar**, sort dropdown, ranked plan cards, compare tray.
- **Sidebar sections** (collapsible, like Oscar): Monthly budget, Excess, Hospital list, Benefits (Must / Nice), Underwriting, Outpatient minimum. Hard requirements show as **locked chips** with "Why locked?" and a button to edit them in the wizard.
- **Sort**: Best match (default), Lowest monthly premium, Lowest excess, Most cover.
- **Card**: plan and insurer name (fictional), monthly premium, excess, hospital list, one headline limit in words, badges (**Best match**, **Lowest premium**), 2–3 plain-English "Why it fits you" chips, Compare checkbox (max 3), **Details**, **Select**.
- **Mobile**: filters in a bottom sheet; compare tray sticky.
- **Empty state**: say which hard requirement removes the plans; offer to relax **only with explicit confirmation**.

**Decision needed (Section 8, D3).** Today the engine returns up to **three** policy families. A filter sidebar is only meaningful with a longer list. Recommended: return a **ranked list of up to ~10 eligible plans**, keep the diversity rule for the **top 3 "Best matches"**, and keep determinism.

**Master prompt.**

```text
Build the Plans page for Helm AI as a separate route (/get-cover/plans) in the Oscar style, using Helm's existing visual tokens.

- Data: extend the recommendations API with a `limit` (default per decision D3) that returns a ranked list of eligible plans, preserving the existing top-3 diversity rule for the "Best match" group, determinism for a fixed profile version, and the rule that hard requirements are never relaxed. Add a `view_filters` object for sidebar filters that narrows/reorders the already-eligible set WITHOUT changing the saved profile.
- Layout: summary strip with Edit (returns to the wizard review), left sidebar with collapsible filter sections (Monthly budget, Excess, Hospital list, Benefits as Must/Nice, Underwriting, Outpatient minimum), sort dropdown (Best match, Lowest monthly premium, Lowest excess, Most cover), list of plan cards, sticky compare tray.
- Hard-requirement filters from the profile appear as locked chips with a "Why locked?" tooltip and an "Edit in my answers" link. A "Save these filters to my answers" button applies sidebar changes as a NEW profile version (with Undo) only after explicit confirmation; otherwise they are view-only.
- Plan card content: plan name, fictional insurer, monthly premium, excess, hospital list, one plain-English headline cover limit, badges (Best match, Lowest premium), 2–3 "Why it fits you" chips generated from deterministic templates, Compare checkbox (max 3, disable the rest with a hint), Details link, Select button.
- Empty state explains which hard requirement eliminated the plans and offers an explicit, confirmed way to adjust it. Never silently relax.
- Responsive: desktop sidebar; at <=768px filters open in a bottom sheet with Apply/Reset; keyboard and screen-reader operable; results count announced via aria-live.
- Performance: filter changes respond within ~300 ms using the server (debounced) or cached data; show skeleton states.
- Tests: filter correctness, sort order, locked chips, empty state, compare limit of 3, no change to saved profile from view-only filters, Playwright desktop + 375px, axe.

Report real results. Stop for approval.
```

**Acceptance.** View-only filters never mutate the profile; Best-match group is deterministic; empty state never relaxes limits silently.

---

### Phase 6 — Plan detail page, plain-English breakdown, per-plan assistant

**Goal.** Replace point scores and flat cap lists with readable text; allow deep Q&A about one plan.

**Build.**
- `/get-cover/plans/:planId` with sections: **Why this plan fits you**, **What's covered**, **What's not covered**, **What you'll pay**, **Conditions and waiting periods**, **Hospital access**, **How we estimate** (methodology link, like Oscar's "See how we estimate").
- **Score → words** (server-side, deterministic). Example from the supplied screenshot: coverage 24.63 of 30 ≈ 82 %, reference value 12.79 of 20 ≈ 64 %, access 15 of 15 = 100 %, transparency 13.5 of 15 = 90 %, service 9.2 of 10 = 92 %, flexibility 8 of 10 = 80 %. Proposed bands (tune in Phase 0): **≥ 90 % Excellent**, **75–89 % Strong**, **55–74 % Fair**, **< 55 % Limited**. Display: "Very good on hospital access and service, strong on cover and flexibility, fair on value for money." Numbers sit behind **Show the numbers**.
- **Limits and exclusions in words.** Example from the screenshot: "Hospital stays and cancer treatment are covered up to £100,000 a year. Scans and tests up to £2,500. Outpatient appointments and mental health up to £1,500 each. Physiotherapy up to £500. Dental, maternity, emergency care, chronic conditions and pre-existing conditions are not included. Existing conditions are not covered. This plan uses a moratorium, and you need a GP referral and authorisation before treatment."
- **What you'll pay** in plain scenarios using the six shared treatment scenarios ("If you needed a knee operation: the plan would pay about £X and you would pay about £Y including the excess").
- **Per-plan assistant** (side panel / bottom sheet): grounded retrieval over this plan's structured data and clause text, **every factual answer cites its field or clause**, refuses and offers "ask a broker" when the data does not contain the answer, runs user scenarios through the deterministic cost engine rather than doing its own arithmetic. Starter prompts: "What's excluded?", "Break down my premium", "What does outpatient cover include?", "What happens if I need a scan?".

**Master prompt.**

```text
Build the Plan Detail page and per-plan assistant for Helm AI.

Page (/get-cover/plans/:planId):
- Sections in this order: Why this plan fits you; What's covered; What's not covered; What you'll pay; Conditions and waiting periods; Hospital access; How we estimate.
- Generate all explanatory text on the SERVER with deterministic templates from structured data (contributions, clauses, limits, exclusions, scenarios). The same profile version must always produce the same text. Provide English plus the existing Arabic/RTL support if the site currently translates this content.
- Convert score contributions to words using documented bands (propose: >=90% Excellent, 75-89% Strong, 55-74% Fair, <55% Limited of each category's maximum) and a sentence template; put raw points and the alpha/weights in a "Show the numbers" disclosure.
- Convert caps/exclusions/underwriting/GP-referral flags into short paragraphs plus a compact "Covered up to / Not included" list. State clearly that existing conditions are never assumed covered.
- "What you'll pay": premium (monthly and annual), tax assumption, excess, copayment, and the six treatment scenarios in plain sentences using integer-pence maths from the existing engine.
- Include a Select button and a Compare checkbox, and a link back to the list that preserves sidebar state.

Per-plan assistant:
- Retrieval over this plan's clauses and structured fields only. Each factual sentence shows a citation (field/clause id). If the data does not contain the answer, say so and offer "Ask a broker about this".
- Scenario questions call the deterministic cost engine; the LLM must not compute money itself. The LLM must not state eligibility or prices that are not returned by the engine.
- Label as general information, not personal advice. Session-only history, bounded length, sanitized rendering, request-limit handling, offline fallback.
- Build an evaluation set of >= 50 questions per two sample plans with expected citations, plus a set of unanswerable questions that must be refused; report pass rates.

Tests: template determinism, band mapping, XSS safety of rendered text, citation presence, refusal behaviour, Playwright desktop + 375px, axe.

Report real results. Stop for approval.
```

**Acceptance.** No page shows raw points by default; assistant refuses unanswerable questions; citations appear on factual answers.

---

### Phase 7 — Compare, select up to 3, review selection

**Goal.** Clear comparison and a safe, explicit selection.

**Build.**
- `/get-cover/compare`: 2–3 columns; a plain-English **"Main differences"** block at the top ("Plan B costs £18 more a month but includes mental health cover; Plan A has the lower excess"), followed by grouped rows (Cost, Cover, Not included, Conditions, Hospital access).
- **Selection** with a counter ("2 of 3 chosen"), reachable from list, detail and compare.
- `/get-cover/selection`: review chosen plans, the **profile summary that will be shared**, and explicit **consent** to share it with the selected insurers (and optionally the broker).
- Backend: extend confirmation to **1–3 plans per comparison**, keeping stale-version checks and idempotency; keep the explicit record that no payment or policy was created.

**Master prompt.**

```text
Implement plan comparison and multi-plan selection.

- Compare page (/get-cover/compare, replacing the current redirect): up to 3 plans side by side with a "Main differences" paragraph generated deterministically from the plans' data, then grouped rows (Cost, Cover, Not included, Conditions, Hospital access). Mobile: swipeable columns or stacked cards with a pinned header.
- Selection: allow choosing up to 3 plans from the list, detail and compare pages; show a counter and prevent a 4th with an explanatory message. Persist selection in the session.
- Review page (/get-cover/selection): show each chosen plan summary, the exact profile fields that will be shared with insurers, and separate consent checkboxes (starting unticked): (a) share my answers with the selected insurers to request quotations, (b) optionally share with a broker. Record consent with timestamp and wording version.
- Backend: adapt /api/v1/quotation/confirm (or add /api/v1/selection) to accept 1-3 plans for one comparison, preserving: session isolation, stale profile-version rejection, idempotency for an identical selection, rejection of conflicting selections, and the receipt statement that no payment, policy creation or account linking occurred. Update docs/QUOTE_WORKFLOW.md.
- Update existing tests that assumed a single selected plan; add tests for 1, 2, 3 and 4 selections, stale versions, idempotency and conflicts.
- Playwright: select from each page, compare, review, consent gating.

Report real results. Stop for approval.
```

**Acceptance.** Cannot continue without at least one plan and the insurer-sharing consent; stale versions rejected.

---

### Phase 8 — Verified contact: WhatsApp number and real one-time password

**Goal.** Verify the visitor's WhatsApp number with a real code sent over WhatsApp.

**Provider guidance (important).**
- Use the **official WhatsApp Business Platform (Cloud API)** *authentication template*, or a verification provider that offers a WhatsApp channel, behind a `OtpDeliveryProvider` interface. Business verification and template approval are required and take real lead time.
- An **MCP server can sit in front of the official API** as a tool interface, but **do not build real-user verification on an unofficial WhatsApp-Web bridge**: it breaks WhatsApp's terms, can get the number banned, and is unreliable.
- Keep a `ConsoleProvider` (dev), an `EmailProvider` fallback, and a sandbox/test-number mode so development never sends to real people.
- Support international numbers: default **+44**, but allow any country code (developers outside the UK need to test).

**Build.**
- `/get-cover/verify`: country-code picker + number, WhatsApp consent text, optional email as backup.
- `/get-cover/verify/code`: 6-box code entry with paste support, resend timer, attempts left, "Use email instead".
- Backend: `POST /api/v1/verify/start`, `POST /api/v1/verify/check`.
- Security: CSPRNG 6-digit code; store only a salted HMAC; 5–10 minute expiry; max 5 attempts; resend cooldown and hourly cap per number, per session and per IP; timing-safe compare; one active code per number; number normalised to E.164; number stored encrypted plus a lookup hash; **no code or number in logs**.

**Master prompt.**

```text
Implement WhatsApp-verified contact capture for Helm AI.

Backend:
- OtpDeliveryProvider interface with implementations: WhatsAppCloudProvider (official WhatsApp Business Platform, authentication template with OTP; configuration via server-side env vars only), ConsoleProvider (dev, prints a masked notice), EmailProvider (fallback) and a sandbox mode that only sends to allow-listed test numbers. If helpful, expose the provider as an MCP tool, but do NOT use an unofficial WhatsApp Web bridge.
- Endpoints: POST /api/v1/verify/start {country_code, number, channel, consent} and POST /api/v1/verify/check {code}. Validate and normalise to E.164 (use the phonenumbers library). Record an explicit WhatsApp-messaging opt-in with timestamp and wording version.
- OTP security: 6 digits from a CSPRNG; store only a salted HMAC; 10-minute expiry; max 5 attempts; 60-second resend cooldown; max 3 sends per hour per number; per-IP and per-session limits; timing-safe comparison; invalidate on success; never log codes or full numbers; encrypt the stored number and keep a keyed hash for lookups.
- On success create a VerifiedContact bound to the research session and the selected plans.
Frontend:
- /get-cover/verify: country picker (default +44), number input with live formatting, consent text, "Send code on WhatsApp" button, optional "Use email instead".
- /get-cover/verify/code: six-digit input with paste/auto-advance, resend countdown, attempts feedback, clear errors, accessible announcements, RTL support.
Tests: unit tests for normalisation, expiry, attempts, cooldown, hashing; integration tests with ConsoleProvider; Playwright for the full flow with a test code; abuse tests (rate limits). Document the live setup checklist (business verification, template approval, phone-number registration, secrets) in docs/.

Report real results and clearly state that real WhatsApp delivery was or was not exercised. Stop for approval.
```

**Acceptance.** Cannot proceed without a verified contact; limits hold under abuse tests; no secrets in logs.

---

### Phase 9 — Link validity, quote requests and the private dashboard

**Goal.** After verification, ask how long the private link should last, generate it, request the quotations, and open the dashboard.

**Build.**
- `/get-cover/access`: two large cards — **24 hours** or **48 hours** — with a plain explanation of what the link is and why it expires.
- Backend creates the **MagicLink** and one **QuoteRequest per selected plan** via an **insurer adapter interface** with a `SimulatedInsurerAdapter` (synthetic quotations after a short delay).
- The link is shown on screen (copy button) **and** sent on WhatsApp (utility template).
- **Token security**: 256-bit random, stored hashed, bound to the verified contact, revocable, expiring at 24/48 h; opening the link shows a short **"Continue to my quotes"** interstitial (so link-preview bots in chat apps cannot consume it), exchanges the token for a short-lived **httpOnly session cookie**, then redirects to `/my-quotes` so the token is not left in the address bar; `Referrer-Policy: no-referrer`; no sensitive data in the URL.
- **Dashboard shell** `/my-quotes`: header with a countdown ("Your link expires in 23 h"), tabs **Quotations · Compare · Ask Helm · Documents · My answers · Broker**, per-plan status (**Requested → Received**) updating by polling/SSE.
- **Expired/revoked** page: friendly explanation and "Get a new link", which requires re-verification by OTP.

**Master prompt.**

```text
Implement the access-link step, quote-request orchestration and dashboard shell.

- /get-cover/access: two cards, "24 hours" and "48 hours", each explaining that the link opens a private dashboard with the user's quotations and will expire. Selecting one calls POST /api/v1/access-links.
- Backend models: MagicLink (token hash, verified_contact_id, session/profile version, expires_at, revoked_at, last_used_at), QuoteRequest (selection id, plan variant id, insurer id, status, requested_at, received_at), Quotation (request id, synthetic quote document and breakdown data, validity, status). Add Alembic migrations.
- Insurer adapter interface InsurerAdapter.request_quote(profile_snapshot, plan) with SimulatedInsurerAdapter that returns deterministic synthetic quotations after a short randomised-but-seeded delay, plus failure/timeout paths. Real adapters can be added later without UI changes. Requests are idempotent per selection and rejected if the profile version is stale.
- Token: 256-bit random, store only a hash, bind to the verified contact, revocable, expiry exactly 24h or 48h from creation, rate-limited lookups. Opening the link shows a "Continue to my quotes" interstitial, then exchanges the token for a short-lived httpOnly SameSite cookie and redirects to /my-quotes with no token in the URL. Set Referrer-Policy: no-referrer and no-store caching on dashboard responses. Never log tokens.
- Deliver the link on screen (copy button) and by WhatsApp using a utility template via the notification service (provider interface mirroring the OTP providers; console/sandbox in dev).
- Dashboard shell with tabs (Quotations, Compare, Ask Helm, Documents, My answers, Broker), an expiry countdown, per-plan request status updating via polling or SSE, loading skeletons, and an expired/revoked page with "Get a new link" requiring OTP re-verification.
- Tests: token expiry, revocation, reuse after expiry, wrong-contact binding, interstitial behaviour, cookie flags, adapter idempotency/timeout, status updates, Playwright from selection to dashboard.

Report real results. Stop for approval.
```

**Acceptance.** Expired/revoked links are rejected; tokens never appear in logs or the address bar after exchange; quotations appear with status updates.

---

### Phase 10 — Dashboard features: breakdowns, comparison, downloads, assistant, reminders

**Goal.** Make the private dashboard genuinely useful.

**Build.**
- **Quotation cards** with a plain-English breakdown: price (monthly/annual, tax), excess, what's included, what's not included, conditions to watch, quote validity.
- **Compare tab**: side by side with a "Main differences" paragraph (same generator as Phase 7, now using actual quotations).
- **Documents tab**: download each quotation as **PDF**, plus a comparison PDF (server-side generation using the project's existing PDF tooling).
- **Ask Helm** (dashboard assistant) with three modes: **Explain** a quotation, **Compare** two or three, and **Recommend**. Recommendations are produced by the **deterministic engine** and narrated by the LLM ("Based on your answers, Plan A fits best because… Things to check… Talk to a broker to confirm"). The assistant cites its sources, refuses what the data cannot support, and never computes money itself.
- **Reminders** via WhatsApp (utility template): when a new quotation arrives and shortly before link expiry; user can opt out. **Extend link** requires OTP re-verification.
- **My answers** tab: read-only profile summary (edits start a new journey/version).

**Master prompt.**

```text
Build the private dashboard features for Helm AI (Phase 10) on top of the Phase 9 shell.

- Quotations tab: card per quotation with plain-English sections (What you'll pay, What's included, What's not included, Things to watch, How long this quote is valid). All text is generated on the server with deterministic templates from Quotation data; numbers are available behind "Show the numbers".
- Compare tab: 2-3 quotations side by side with a deterministic "Main differences" paragraph (reuse the Phase 7 generator).
- Documents tab: generate downloadable PDFs for each quotation and for the comparison on the server using the repo's existing PDF dependencies. Include the synthetic/demo disclosure, profile version and generation time. Downloads are authorised by the dashboard session cookie only.
- Ask Helm assistant: modes Explain, Compare, Recommend. Retrieval is limited to this user's profile snapshot, their quotations and approved glossary content. The deterministic engine produces any ranking or money figure; the LLM only narrates. Every factual statement carries a citation; unanswerable questions are refused with an offer to contact a broker; add a clear "general information, not personal advice" label. Session-only history, bounded, sanitized rendering, rate limits, offline fallback, per-message consent for provider calls with a deterministic fallback.
- Reminders: notification service jobs for "new quotation received" and "link expires soon" (WhatsApp utility template via provider interface; console/sandbox in dev), with opt-out recorded. Extending the link requires OTP re-verification and creates a new expiry (24 or 48h) without re-issuing the old token.
- My answers tab: read-only summary of the profile snapshot used for the quotations.
- Tests: PDF content checks, authorisation (no access without the session cookie or after expiry), assistant evaluation set (explain/compare/recommend plus refusals), reminder scheduling idempotency, Playwright desktop + 375px, axe.

Report real results. Stop for approval.
```

**Acceptance.** PDFs download only with a valid dashboard session; recommendations always trace to the deterministic engine; reminders are idempotent and opt-out works.

---

### Phase 11 — Broker contact, case creation and Broker Workspace

**Goal.** Let a visitor reach a broker at any point, and give brokers a workspace with the whole picture.

**Build.**
- **Contact a broker** floating action on every step, plan page and dashboard tab; opens a short panel: preferred channel (WhatsApp/email/call-back), best time, optional note, **consent to share profile and selected plans with the broker**.
- **Case** with a state machine: `new → triaged → in_progress → awaiting_customer → awaiting_insurer → ready_for_signoff → submitted → closed`, explicit allowed transitions, and an append-only audit log (`CaseEvent`).
- **Automatic case creation after plan selection** (decision D5: always, or only when the visitor opts in at the selection consent).
- **Case summary** generated for the broker: customer profile, hard limits vs preferences, shortlisted and selected plans with plain-English reasons, quotations received, contact channel, consents, open questions the visitor flagged.
- **Notification** to the broker by workspace inbox plus email/WhatsApp (sandbox adapters).
- **Broker Workspace** (restore from `archive/` or rebuild — decision D4): separate authenticated entry point, broker roles, assignment, multi-client queue with filters (status, urgency, expiry), case detail, message thread, notes, documents.
- **Access control** enforced server-side: a broker sees only assigned cases, and only after consent.

**Master prompt.**

```text
Implement broker contact, case creation and the Broker Workspace for Helm AI.

- Visitor side: a floating "Talk to a broker" action on every wizard step, plans/detail/compare pages and dashboard tabs. It opens a panel capturing preferred channel (WhatsApp, email, call-back), best time, optional note, and an explicit, unticked consent to share the profile and selected plans with a broker. Record consent with timestamp and wording version. Revocation is supported.
- Case model and state machine: new, triaged, in_progress, awaiting_customer, awaiting_insurer, ready_for_signoff, submitted, closed, with a transition table enforced on the server and an append-only CaseEvent audit log. Create a case on broker request and (per decision D5) automatically after plan selection when consent exists.
- Case summary generator (deterministic data assembly; an optional LLM paragraph is allowed only as a draft clearly marked as AI-drafted): profile with hard limits vs preferences, shortlisted/selected plans and reasons, received quotations, contact preferences, consents, flagged questions, link expiry.
- Notifications: workspace inbox item plus email/WhatsApp through sandbox provider adapters.
- Broker Workspace: decide between restoring the archived workspace (see archive/README.md and archive/MANIFEST.md) and rebuilding; implement as a separate authenticated entry point with broker roles, case assignment, a multi-client queue with filters (status, urgency, link/quote expiry), case detail, message thread with the customer, notes and a documents area. Reuse the existing authorization patterns; do not weaken any existing access control.
- Access control: server-side, per-case; a broker can access only assigned cases and only with recorded consent.
- Tests: role-based access, consent gating, transition rules, audit trail completeness, notification adapters, Playwright for visitor request -> case appears in workspace.

Report real results. Stop for approval.
```

**Acceptance.** No broker access without consent and assignment; every transition is audited.

---

### Phase 12 — Broker AI assistant (human in the loop)

**Goal.** One broker handles many clients; the AI prepares, the human decides and signs.

**Build.**
- Per-case and cross-queue assistant: summarise, flag missing items, prioritise by urgency/expiry.
- **Drafts only, never submits**: customer-needs summary (a "demands and needs" style statement), recommendation rationale, quotation comparison, application/underwriting pack for the chosen insurer, customer messages, follow-up reminders.
- **Configurable compliance checklist** per case (required documents/disclosures) with each item marked *drafted / missing / conflicting*. Treat real regulatory content as a placeholder until legal review; make **no compliance claims**.
- **Source-linked drafts**: each statement links to the profile field, clause or quotation it came from; low-confidence statements are highlighted.
- **Sign-off workflow**: review, edit, approve; approval records user, time and document version; only approved documents can be sent or exported. Bulk actions only for non-risky steps (for example reminders), never for approvals.
- **Full AI audit log**: model, prompt version, inputs referenced, output hash.

**Master prompt.**

```text
Build the Broker AI assistant for Helm AI with strict human-in-the-loop controls.

- Provide per-case actions: Summarise case, Find gaps, Draft needs summary, Draft recommendation rationale, Compare quotations, Prepare insurer application/underwriting pack, Draft customer message, Schedule follow-up. Provide a queue view that ranks cases by urgency (link/quote expiry, awaiting status) and shows what the assistant has prepared.
- Every generated document is a DRAFT with: source links (profile field, clause or quotation ids) for each statement, highlighted low-confidence items, and a visible "AI-drafted, needs broker review" label. The assistant cannot send, submit or export a draft.
- Implement a configurable compliance checklist engine (data-driven JSON/YAML) per case type. The AI marks items drafted/missing/conflicting. Real regulatory wording is placeholder content pending legal review; never state or imply that Helm is FCA-authorised or that a document is compliant.
- Sign-off workflow: the broker reviews, edits, and approves; approval stores broker id, timestamp, document version hash and the checklist state. Only approved versions can be sent to the customer or exported. Rejections capture edit notes. Bulk operations are allowed only for non-risky actions (e.g. reminders), never for approvals.
- Audit: store model, prompt version, input references and output hash for every generation. Drafts must be reproducible from their referenced inputs.
- Safety: user-supplied text is data (prompt-injection safe); no invented facts: build an evaluation set of cases with known facts and measure fabricated-statement rate (target zero in the evaluated set; report the actual number).
- Tests: approval gating, audit completeness, draft-to-source traceability, refusal to send unapproved documents, role access, Playwright broker flow.

Report real results. Stop for approval.
```

**Acceptance.** No document leaves the system without recorded human approval; drafts trace to sources; evaluation reports fabricated-statement rate.

---

### Phase 13 — Hardening, QA and launch-readiness review

**Build / verify.**
- Update every Playwright/unit test that targeted the old page; keep the legacy page behind the flag until sign-off, then remove it deliberately.
- **Funnel analytics** (privacy-safe, no answers or PII): step views, step completion, drop-off per step, mode chosen, "Show my plans" clicks (checkpoint vs optional), plans viewed, selections, OTP success rate, link choice (24 vs 48), dashboard opens, broker requests.
- Physical-device checks (mobile scrolling, keyboards), manual screen-reader pass, keyboard-only pass, zoom/reflow, Arabic wording review, performance budgets re-measured.
- Security review: OTP and magic-link abuse tests, session cookie flags, CSRF, rate limits at the edge, dependency audit, secrets scan.
- Privacy review: data map, retention periods, deletion/export for the visitor, processor list (LLM, WhatsApp provider), consent wording versions.
- Live-integration plan: real insurers, WhatsApp production number, email, storage; update `docs/uk/LAUNCH_READINESS.md`.
- **The production guard stays failing** unless you explicitly approve its removal.

**Master prompt.**

```text
Run a hardening and readiness pass for the Helm AI guided journey. Do not remove the production guard.

1. Update and run all tests: frontend unit, backend pytest, ruff, UK Playwright suite (new wizard, plans, detail, compare, selection, verify, access, dashboard, broker), axe checks. Restart the isolated API between repeated browser runs; do not weaken the request limiter.
2. Add privacy-safe funnel analytics (no answers, no PII) and a short report template for drop-off per step.
3. Produce a manual QA checklist for physical devices, screen readers, keyboard-only, zoom/reflow, RTL and dark mode, and record what was and was not executed.
4. Perform and document a security review (OTP/magic-link abuse, cookies, CSRF, rate limits, secrets scan, dependency audit) and a privacy review (data map, retention, deletion/export, processors, consent versions).
5. Update docs/uk/LAUNCH_READINESS.md, PROJECT_OVERVIEW.md, docs/QUOTE_WORKFLOW.md and AGENTS.md. Remove the legacy one-page form only if I explicitly approve.
6. Report precisely: commands run, real results, unverified items, remaining blockers.
```

---

## 7. Cross-cutting requirements

### 7.1 Data model additions (confirm in Phase 0)

`WizardProgress` (optional, derived), `IntakeTurn` (session-only), `Selection` (1–3 plans), `ConsentRecord` (type, wording version, timestamp), `VerifiedContact` (encrypted number, lookup hash, channel, verified_at), `OtpChallenge` (HMAC, expiry, attempts), `MagicLink`, `QuoteRequest`, `Quotation`, `Notification`, `Case`, `CaseEvent`, `BrokerUser`, `Assignment`, `Document` (versioned, approval status), `Message`, `AIGeneration` (audit).

### 7.2 New or changed API surface (proposed)

| Endpoint | Purpose |
| --- | --- |
| `POST /api/v1/intake/turn` | AI-assisted intake turn |
| `GET /api/v1/recommendations?limit=&view_filters=` | Ranked list + view-only filters |
| `GET /api/v1/plans/{id}/explanation` | Deterministic plain-English sections |
| `POST /api/v1/plans/{id}/chat` | Per-plan grounded assistant |
| `POST /api/v1/selection` | Select 1–3 plans with consent |
| `POST /api/v1/verify/start`, `/verify/check` | WhatsApp OTP |
| `POST /api/v1/access-links` | Create 24 h / 48 h link |
| `POST /api/v1/access-links/exchange` | Token → session cookie |
| `GET /api/v1/dashboard/*` | Quotations, compare, documents, answers |
| `POST /api/v1/dashboard/chat` | Dashboard assistant |
| `POST /api/v1/broker-requests`, `/api/v1/cases/*` | Broker contact and workspace |

### 7.3 Security and privacy (every phase)

UK-GDPR posture; data minimisation; special-category caution for health-related preferences (explicit consent, no sending to providers without per-message consent); encryption of contact data; server-side authorisation on every endpoint; rate limits; no PII, tokens or codes in logs; sanitized rendering; retention periods defined; visitor export and deletion.

### 7.4 Compliance caution

Real FCA authorisation, regulated advice vs information, insurance-distribution disclosures, WhatsApp business-messaging rules and any use of real customer data require **legal review**. This plan keeps everything demo-grade and claims nothing about compliance. Note that live insurers do not typically hand quotations to consumers over WhatsApp; quotations normally flow through a broker or an insurer portal, so the broker path is the realistic route to live quotes.

### 7.5 Testing and rollout

Per-phase unit, integration and Playwright tests plus axe; a visual-regression baseline from Phase 0; staged rollout behind `VITE_QUOTE_WIZARD` with the legacy page as fallback; report only real test results.

---

## 8. Open decisions

| ID | Decision | Recommendation |
| --- | --- | --- |
| D1 | Final order of optional questions | As in Section 5; confirm in Phase 0 |
| D2 | Benefit grouping across three screens | As in 5.1 |
| D3 | Plans list length (engine returns ≤3 today) | Ranked list of ~10, top-3 "Best match" with the existing diversity rule |
| D4 | Broker Workspace: restore from `archive/` or rebuild | Decide after the Phase 0 audit |
| D5 | Auto-create broker case after selection vs opt-in | Opt-in via a clear line in the selection consent |
| D6 | OTP provider | Official WhatsApp Business Platform (or a verification provider with a WhatsApp channel); never an unofficial bridge |
| D7 | LLM provider for intake and assistants | Keep Groq as the first provider behind an interface; add another by configuration |
| D8 | Score-to-words bands | ≥90 / 75–89 / 55–74 / <55 % (tune with real examples) |
| D9 | Treatment of the existing 7-essentials side panel | Replace with the checkpoint screen and Check-your-answers page |

---

## 9. Verification against the brief

### 9.1 Requirement traceability

| Requirement (from the chat and screenshots) | Covered in |
| --- | --- |
| Stop coding; plan only | Section 0; Phase 0 is read-only |
| Oscar-style, one step after another, clean pages | Sections 2–4; Phases 1–3 |
| Keep Helm colours, fonts, style | Invariants 1.3; Phase 0 token capture; every master prompt |
| Keep the same (FCA-based) questions | Invariants 1.3; Section 5; Phase 2 contract test |
| First choose manual or LLM filling | Phase 1 (chooser); Phase 4 |
| LLM asks the same questions with simple answers (numbers, yes/no, names) | Phase 4 |
| Say which questions are optional | Section 5; Phases 3 and 4 |
| "Show plans" appears once optional questions start | Phase 2 checkpoint; Phase 3 persistent button |
| Plans, details etc. on different pages, not one | Section 3; Phases 5–7 |
| Left-hand filter/dropdown adjustment like the reference | Phase 5 |
| Textual breakdown instead of numeric/analytic | Phase 6; Phase 10 |
| Select max 3 plans | Phases 5–7 |
| WhatsApp number prompt | Phase 8 |
| Real WhatsApp (MCP) one-time password | Phase 8 (official API behind an interface; MCP wrapper optional) |
| Magic link with 24 h or 48 h choice | Phase 9 |
| Private dashboard with all quotations and breakdown | Phases 9–10 |
| LLM chatbot for answers, comparison, recommendation on dashboard | Phase 10 |
| Quotations via WhatsApp/email, download, compare | Phases 9–10 |
| Reminder and magic link | Phases 9–10 |
| Contact-a-broker at any time; case to Broker Workspace | Phase 11 |
| Broker gets summary, contacts, preferences | Phase 11 |
| Broker AI drafts documents/reports/underwriting/compliance; human signs off | Phase 12 |
| Per-policy chatbot explaining the whole policy | Phase 6 |

### 9.2 Gaps found on review and added

1. **Engine returns only ≤3 plans**, which makes a filter sidebar and "select up to 3" awkward → added the ranked-list change (D3) to Phase 5.
2. **Confirmation supports one selected plan** → Phase 7 now extends confirmation to 1–3 plans and updates the docs and tests.
3. **`/get-cover/compare` currently redirects to the quote page** → Section 3 and Phase 7 replace it and require a docs update.
4. **Mandatory-first ordering** differs from the current form order → Section 5 re-orders and Phase 2 adds a payload-equality contract test.
5. **Sidebar filters vs confirmed profile** could silently change hard requirements → Phase 5 makes filters view-only with an explicit "save to my answers" step.
6. **Oscar's "Savings" stage has no UK meaning** → mapped to "Fine-tune (optional)" in Section 2.
7. **Dropdown values must not change** → Section 4 rule 2 and the Phase 2 prompt.
8. **Consent semantics** for health-related preferences → preserved in Step 1 and Phase 4 per-message provider consent.
9. **Link-preview bots could consume magic links** and tokens leak via URL/referrer → interstitial, cookie exchange, no-referrer in Phase 9.
10. **Developers outside the UK need to test OTP** → country picker with +44 default in Phase 8.
11. **WhatsApp template approval and business verification** have lead time → documented in Phase 8; sandbox mode for development.
12. **Unofficial WhatsApp bridges** are risky for real users → explicit warning and official-API-behind-an-interface design.
13. **Dashboard expiry and recovery** were unspecified → expired page, OTP-gated new link and extension in Phases 9–10.
14. **Existing Playwright suites target the old page** → listed in Phase 0, updated in Phase 13, with a flag-controlled fallback.
15. **No way to measure whether the redesign works** → privacy-safe funnel analytics added in Phase 13.
16. **"Save draft", Undo and profile history** exist today → preserved in Phase 3.
17. **Accessibility, RTL, dark mode, reduced motion** → carried as rules in Section 4 and every prompt.
18. **Demo vs real data**: real OTPs mean collecting a real phone number even in a demo → consent, retention and deletion are required in Phases 8 and 13.

### 9.3 What this review could not verify

- The screenshots show the form but not the code: field keys, validation, the exact "essentials confirmed" rule and the real option values are assumptions until **Phase 0** checks them.
- Only the first step of Oscar's live site was reachable; the rest of that flow was inferred from your screenshots.
- No `.pdf` file arrived with the last upload (the first attachment is a full-page screenshot named like a PDF export), so nothing beyond the three images was reviewed.
- Third-party requirements (WhatsApp approvals, provider terms, FCA position) must be confirmed with the providers and with legal advice before any live use.
