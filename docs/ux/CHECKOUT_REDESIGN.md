# Selection review and essentials checkpoint

## Audit and design plan — 25 October 2026

The attached brief is the design specification. Canonical profiles, three-plan selection limit, insurer/broker consent API contracts, edit destinations and demo WhatsApp authentication stay intact. This is a presentation change, not a new checkout/payment or real insurer submission.

Source palette: `frontend/src/ui/uk.css` defines teal `--uk-teal: #053b44`, mint `--uk-mint: #e4f6f3`, paper `--uk-cream: #f6f3ee`, ink `--uk-ink: #172c32`, muted `--uk-muted: #52666a`, indigo `--uk-brand: #4b4dff`, line `--uk-line: #c9d4d3`. `journey.css` adds navy `--j-navy: #142c43`, focus teal `--j-teal: #087c7a`, and white surfaces. Existing muted error colors remain. No new hue, gradient or font is needed. Inter is the UI family; Instrument Serif remains the marketing display family. Checkout headings use Inter with restrained tracking rather than the global hero scale.

Stack/components: React Router, TypeScript, plain scoped CSS, lucide-react, existing Modal, BrokerContact, PrivacyControls, journey API and useWizardProfile. Reuse native details, definition lists, forms and external form buttons. Add only shared presentation helpers, detail rows, stepper and action layout. No dependencies.

Files in scope: `uk/Shell.tsx`; wizard `PlansApp.tsx`, `SelectionReview.tsx`, `WizardApp.tsx`, `StepFields.tsx`; new checkout/profile/checkpoint presentation files and scoped CSS; relevant unit/browser tests and this evidence document. Other routes retain their marketing shell. All current legal links, regulatory text, fictional-product and demo notices remain.

Type scale: 14px supporting text, 16px body/consent, 18px panel headings, 24px plan names, 32–40px H1, 44px premium. Money uses tabular numerals. Spacing follows 8px steps, 24–32px between groups. Only the plan summary has a shadow; flat details use hairlines. Panels use 12px radii and controls 8px. State feedback is 160ms, disabled for reduced motion.

```text
Desktop, max 1120px
  Logo                                  Save and exit   Help
  Plans [done]      Compare [link]       Review [current]
  Review your choice
  Household / region / formatted start              Edit my answers
  +----------------------------------+  +----------------------------+
  | Must-haves + explanation          |  | Plan name (demo)           |
  | Your details                     |  | £95.86 / month             |
  | Label       Value        Edit    |  | Excess / insurer / details |
  | Label       Value        Edit    |  | Required sharing consent   |
  | Exact shared profile disclosure  |  | Optional broker consent    |
  |                                  |  | Request my quote + help    |
  +----------------------------------+  +----------------------------+
  Compact legal links and complete regulatory disclaimer

Mobile
  Logo                         Save and exit   Help
  Stepper / heading / household
  Plan summary, clear price and excess
  Required and optional consent beside the action
  Must-haves / editable details / exact shared fields
  [price or selection count | Request my quote] fixed bottom action
```

Checkpoint: full 7/7 progress, one H1, quiet saved status, a flat definition-list summary and collapsed unused benefit rows. Primary **See my plans** and secondary **Add optional details (about 2 min)** stay visually grouped. Existing confirmation and recommendation generation remain the primary action's implementation.

The generic review/rating layout suggested by the design lookup was rejected: no ratings, promotional testimonials, new colors, new fonts or uniform card grid. The design is based on the actual insurance selection task.

## Product wording decisions

Use **Request my quote** (plural for multiple selected plans), as requested. It still records consent/selection and proceeds to demo phone verification; it does not create a real quotation or payment. Supporting text explains this. The slim shell is scoped to `/get-cover/selection` and `/get-cover/quote/ready`; all other marketing navigation remains. These decisions are reviewable in the running prototype without blocking development.

The requested disabled-but-pressable consent action uses `aria-disabled` until required consent is accepted. It remains keyboard focusable so an attempted activation can explain the missing consent and focus its checkbox. The submit handler refuses all consent/selection API calls until consent is accepted. Busy/no-plan actions use native disabled state.

## Verification and before/after checklist

| Before | After |
|---|---|
| Competing “Explore your choices” and review headings | One “Review your choice” H1 and a real navigation stepper; comparison remains optional rather than falsely marked complete |
| Price, excess and insurer buried in a sentence | One elevated plan panel, 44px tabular premium, labelled excess/insurer/hospital rows, internal catalogue name inside Plan details |
| Long unstructured label/value text and scattered edits | Shared flat definition-list rows with one labelled pencil action per field; all original edit destinations retained |
| Plan and consent separated by the entire profile | Consent is inside the selected-plan panel; required/optional wording remains unchanged; mobile has a fixed price/action bar |
| Bottom navigation mixed with broker action | Navigation moves to the stepper; broker help stays separate beside the confirmation area |
| Marketing navigation, hero footer and content assistant button compete | Two exact routes use a slim logo/save/help header and compact legal footer; the assistant still opens from Help and all regulatory text remains |
| Grey disabled action with no explanation | Muted navy/white, visible consent helper, focusable aria-disabled guard, inline error linked to checkbox, loading spinner and retry state |
| Tiny consent controls and low-priority text | 16px legal consent, 44px minimum labelled targets, explicit focus rings and keyboard-friendly disclosures |
| Checkpoint primary action below long summary | Both next actions appear before the summary; See my plans is visible at 360px without scrolling; complete 7/7 progress and a quiet lock/saved status |
| “1 adults”, zero children, ISO dates and “of3” | Shared plural/date formatting, hidden zero counts, “1 of 3 plans chosen” |
| Joined “excess£…” and “insurerins-…” metadata | Independent labelled rows; whole-pound excess and full-precision monthly premium |
| Research/Tier/List codes presented as the plan title | Display-only Health plan N name; canonical name/version and actual IDs unchanged and available in details |
| “lead adult: 18”, unlabelled budget/excess and repeated none rows | “Adult, age 18”, separate Budget/Excess rows, Standard/Broader (demo), collapsed Optional (none added) group |
| Hard-requirement jargon and crowded heading rendering | Plain must-haves strip with What does this mean; full details expand without losing constraints; scoped Inter type scale/normal kerning and restrained tracking |

Critique removed the redundant parent hero heading and the competing bottom tab/action strip. The obsolete checkpoint branch in StepFields was also removed rather than leaving a second implementation. A pre-existing wizard width/heading rule initially narrowed the new page; it now explicitly excludes checkout layouts. The mobile action focuses and centers the required checkbox when activated without consent, keeping it above the fixed bar. Save and exit uses a native external form button and flushes the existing draft before leaving; the session capability remains in the same browser tab.

Font investigation found existing Inter 400/500/600 font faces and global hero heading rules with negative tracking. The new headings explicitly retain Inter, normal kerning and -0.015em tracking. No font download, font-family replacement or display-font dependency was introduced.

Actual checks: frontend TypeScript check and scoped ESLint passed; Vitest **21 passed**, including five new formatting/constraint-display cases. Browser checks passed **19 distinct scenarios** across focused batches: checkout7, existing selection2, mandatory/shell journey3, guided2, optional2 and provider/demo UI3. Final layout/axe checks cover 360, 768, 1024 and 1440px; existing journeys also cover 375px. Dark OS preference and reduced motion are included. Consent-disabled/ticked/error/loading/retry states, optional broker opt-in then opt-out, selection receipt, disclosures, saving, help, existing edit routes, session preservation and canonical profile values are exercised. The first axe pass caught the exact-fields scroll region missing keyboard access; added a focusable labelled region and reran successfully. Old guided assertions expected the deliberately replaced “lead adult: 35” text; updated them to “Adult, age 35” and reran both widths. No protections were weakened or failing behavior hidden.

Measured contrast: disabled navy/white **6.39:1**, muted text/paper **5.47:1**, teal/mint **10.94:1**. Axe reported no serious/critical issues in the tested main content. Screenshot evidence was visually checked at desktop and mobile; before/after PNGs are local, ignored `.runtime/checkout-before-*`, `.runtime/checkout-ready-*`, `.runtime/checkout-review-*` and `.runtime/checkout-loading-*` files. Browser automation is not a manual screen-reader or physical-device audit.

Final flag-on demo build passed, including TypeScript and the existing public-source guard. Two additional smoke checks against the built preview at 4174 and actual local demo API passed at 1440px and 360px: visible checkpoint action, loaded Inter font, one review heading aligned to the content edge, 1120px desktop width, no horizontal overflow, and consent gating. Normal API was restored in mock mode with real_delivery=false. No live provider, database migration or production release was exercised.

Modified source: `frontend/src/uk/Shell.tsx`; `frontend/src/journey/wizard/PlansApp.tsx`, `SelectionReview.tsx`, `WizardApp.tsx`, `StepFields.tsx`, `wizard.css`; new `Checkout.tsx`, `Checkpoint.tsx`, `ProfileSummary.tsx`, `checkout.css`, `checkoutPresentation.ts`. Tests: new `checkoutPresentation.test.tsx` and `tests/wizard/checkout.spec.ts`, updated selection/journey/guided specs. Documentation: this file and WIZARD_PROGRESS.md. No backend, database schema, dependency, palette or authentication-provider changes.

Product review points: **Request my quote(s)** remains the brief's proposed label for selection/consent followed by demo verification; **See my plans** now precedes checkpoint details to keep the next action visible. The slim header/footer are enabled only on the two requested routes. All are implemented and reviewable, with no live insurer transaction or production release implied.
