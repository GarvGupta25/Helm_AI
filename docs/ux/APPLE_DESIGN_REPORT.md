# Apple design pass — local review report

Branch: **apple-design-pass**. Base: local main **d0807c7**. Author: Utkarsh Raj. No push, force-push, merge, PR or deployment was performed. The owner requested local review and an exact `approved: push` before publishing the branch. That restriction supersedes the older shared-repo push workflow.

## Skill and scope

Installed for this project with `npx skills add emilkowalski/skills --skill apple-design -a codex -y`. Source: https://github.com/emilkowalski/skills. Complete file read: `.agents/skills/apple-design/SKILL.md`; no companion file references exist in it. `skills-lock.json` records the source/hash. AGENTS.md contains the exact requested line: `For any UI work, use the apple-design skill.`

The 17 principles are response, direct manipulation, interruptibility, springs, velocity handoff, momentum projection, spatial consistency, directional hints, rubber-banding, gesture thresholds, frame-level smoothness, material hierarchy, useful multimodal feedback, accessibility preferences, size-aware typography, the eight design foundations, and interactive iteration/testing.

Numbers match the brief: press .97/100ms; default damping1/response.3–.4; reposition1/.4; rotation.8/.4; sheet.8/.3 after a momentum gesture; rubberband.55; drag threshold10px; projection d=.998; blur20px/saturate180%; large heading tracking-.02em. The skill says bounce only after a gesture: programmatic sheet entrance/close therefore use damping1, with .8/.3 on a moving release. The skill also suggests blur animation, but the owner's transform/opacity-only requirement takes precedence. Brand font retention likewise overrides the skill's generic system-font preference.

No product copy, routes, backend, data fetching, ranking, consent, account roles, phone verification or business logic was changed. No runtime dependency was added. `npx skills` was an installation tool; it did not add a frontend package. Static cards remain static; real interactive cards receive feedback through their existing button/anchor semantics. Actions still commit on normal click/up, never on pointer-down.

## Per-task commits and files

### 36a863c chore(ui): install project apple-design skill and guidance

`.agents/skills/apple-design/SKILL.md`, `AGENTS.md`, `skills-lock.json`

### 22e771f fix(ui): address five motion and dialog audit findings

`frontend/src/broker/main.tsx`, `frontend/src/main.tsx`, `frontend/src/ui/apple-design.css`

### 386f50c feat(ui): unify immediate cancelable press feedback

`frontend/src/broker/main.tsx`, `frontend/src/main.tsx`, `frontend/src/ui/PressFeedback.test.tsx`, `frontend/src/ui/PressFeedback.tsx`, `frontend/src/ui/apple-design.css`

### 25e59e4 feat(ui): add interruptible gesture sheet to shared dialogs

`frontend/src/ui/SheetModal.tsx`, `frontend/src/ui/apple-design.css`, `frontend/src/ui/primitives.test.tsx`, `frontend/src/ui/primitives.tsx`, `frontend/src/ui/spring.test.tsx`, `frontend/src/ui/spring.ts`, `playwright.apple.config.ts`, `tests/apple/motion.spec.ts`

### 5e8e238 refactor(ui): use spring curves for compositor transitions

`frontend/src/broker/workspace.css`, `frontend/src/foundation.css`, `frontend/src/journey/journey.css`, `frontend/src/journey/wizard/checkout.css`, `frontend/src/journey/wizard/wizard.css`, `frontend/src/marketing/chat/chat.css`, `frontend/src/marketing/components/ChatPanel.css`, `frontend/src/marketing/components/MarketingLayout.css`, `frontend/src/marketing/marketing.css`, `frontend/src/marketing/pages/ContactPage.css`, `frontend/src/marketing/pages/HomePage.css`, `frontend/src/marketing/pages/PartnersPage.css`, `frontend/src/marketing/pages/PlanDetailPage.css`, `frontend/src/marketing/pages/PlansPage.css`, `frontend/src/member/member.css`, `frontend/src/styles.css`, `frontend/src/ui/apple-design.css`, `frontend/src/ui/uk.css`, `frontend/src/uk/home.css`, `frontend/src/uk/site.css`

### b56d850 style(ui): add single-layer navbar glass and optical headline spacing

`frontend/src/ui/apple-design.css`

### Task6 — Accessibility and final checks (current HEAD after commit)

Files: `frontend/src/ui/SheetModal.tsx`, `frontend/src/ui/apple-design.css`, `tests/apple/motion.spec.ts`, `docs/ux/APPLE_DESIGN_REPORT.md`.

Motion preference removes travel and bounce, including live changes while the sheet is active, and uses a short opacity spring/fade. Transparency preference switches navbar glass to opaque brand surfaces. Contrast-more adds solid material, clearer borders/text/focus. Forced-colors uses Canvas/CanvasText/ButtonText. Unsupported backdrop-filter falls back to opaque navigation; the default supported glass is already near-opaque for browsers without a transparency-preference signal. JS checks all three media queries and subscribes to their changes. Mobile sheet sizing uses border-box to keep padding inside the viewport.

The audit is intentionally **untracked** at `audit/APPLE_DESIGN_AUDIT.md`. Do not stage it. The six task commits are separate from the skill/AGENTS setup commit; use `git log --oneline main..apple-design-pass` for all seven hashes.

## Implementation choices and differences

- Shared Radix Dialog remains responsible for modal semantics, focus trapping, Escape, outside dismissal and restoration. It stays mounted/modal through visual exit. A drag handle adds pointer capture, a10px threshold,1:1 movement, .55 rubber-banding, recent velocity sampling and projected landing. Content remains normally scrollable/selectable. A moving close can be grabbed and reversed before it unmounts. On phone-sized screens it anchors at the bottom; desktop retains the centered dialog footprint.
- Gesture springs use a small native requestAnimationFrame controller with the closed-form damped oscillator. Retargeting keeps presentation position/velocity. Numeric tests cover monotonic critical settling, continuous retargeting, momentum overshoot, rubberband sign/resistance and projection.
- Non-gesture transitions use a precomputed critical spring `linear()` curve from response.35s. `--apple-ui-time:600ms` and `--apple-move-time:700ms` are finite sampling windows for the physical curve, not ease-based gesture durations; press keeps the explicitly requested100ms window. The gesture solver has no duration. Browsers without CSS linear()/independent scale support degrade to immediate visual changes; input still works. Older Safari/Firefox behavior needs manual verification.
- State-driven motion interpolates transform/opacity and the independent compositor scale property. Hover/focus color, border and shadow changes are immediate. The older scheme-card stripe now scales rather than animating width. No backdrop-filter animation was added. Paint/layout/ease transition scan over all app-owned CSS found zero remaining such transition declarations.
- Infinite loading spinners and activity pulses retain linear/time-based loops because they report ongoing work rather than settling toward a target. Reduced motion stops them. Decorative hero zoom, arrow bounce and badge rotation were removed. Lottie/Embla/Radix widget internals were left unchanged; existing reduced-motion-aware Lottie playback remains.
- The navbar is one glass layer; menus and sheets are solid and the scrim is dimming-only. Existing navbar footprint, scroll/pill behavior, routes, colors and fonts remain. Heading tracking/leading changes apply only to headings/display numerals; body typography remains unchanged. Inline links get a transformable box while their existing flex/grid/block styles retain priority.
- The early tests caught a portal-mount timing bug, a press-selector specificity conflict and content-box sheet overflow. Fixed each cause and reran. A mid-close capture test uses a controlled browser clock to catch an exact frame instead of racing a moving handle. The first typography test sampled before the lazy home content mounted; it now waits for the heading. A cold dev-route check saw a resource404; subsequent full route/console checks passed. No error filter hides browser errors.

## Verification

- `npm --prefix frontend run check`: passed.
- `npm --prefix frontend run lint:uk`: passed.
- `npm --prefix frontend run test`: **27 passed** across9 files.
- `$env:VITE_QUOTE_WIZARD='true'; npm --prefix frontend run build`: passed, including tsc and existing demo release guard. Existing Home.tsx mixed static/dynamic-import chunk warning remains; it is not a runtime error or new dependency.
- `npx playwright test --config playwright.apple.config.ts`: **7 passed**. Native press-before-release, cancel-away, desktop/mobile sheet tracking/resistance/Escape/bounds, closing reversal and dismissal, reduced-motion/live changes, glass/type/transparency/contrast and no browser console errors on dev routes/dialogs.
- Existing wizard checkout/selection/broker-contact batch: **10 passed**. Includes360/768/1024/1440 layouts, consent disabled/error/loading/retry, exact-field disclosure, save/help, multiple selected plans, demo verification destination and broker consent/withdrawal.
- Existing public regression subset: **8 passed**. Home/About375/768/1280/1920, keyboard menus/search/cookies/external-link guard, mobile focus trap/reduced-motion loops, and scroll geometry at375/1280. Generated tracked screenshot artifacts were restored; only intentional source/tests/report are committed.
- Focused axe scans on the shared sheet and existing checkout scans reported no serious/critical violations.
- Final runtime is the built preview at127.0.0.1:4174 plus isolated demo API8000 and local synthetic worker. Real messaging remains disabled. No backend suite/live services were exercised because backend code was untouched. The full customer/broker/UK end-to-end suite was not rerun; selected existing regressions above were run.

## Six-item review checklist

| Item | Status | Evidence / remaining limit |
|---|---|---|
| Press and hold shrinks before release | VERIFIED IN CODE | Browser holds mouse down, observes data-pressed and scale.97, and asserts dialog/action has not committed; phone touch latency needs manual check |
| Close halfway, reverse from current position | VERIFIED IN CODE | Captures an in-flight frame, grabs handle, reverses and remains open; solver preserves position/velocity |
| Flick drawer keeps speed and settles with slight bounce | VERIFIED IN CODE | Recent velocity passes to .8/.3 spring and projection; numeric overshoot test and browser dismiss path; tactile momentum needs manual check |
| Drag past top resists and springs back | VERIFIED IN CODE | Browser checks sub-threshold stability,1:1 positive drag and bounded negative rubberband before settling |
| Reduce Motion makes quick fades | VERIFIED IN CODE | Media emulation and live change keep y=0, disable drag and close via opacity; OS/Safari test remains manual |
| Biggest headline has tighter tracking than body | VERIFIED IN CODE | Browser measures large H1 tracking/fontSize=-.02 and leading1.05; body styles unchanged |

## Review locally

PowerShell from `U:\projects\Helm_AI`:

```powershell
git branch --show-current
git log --oneline main..apple-design-pass
git diff --stat main...apple-design-pass
git diff main...apple-design-pass
# Terminal1 (if API8000 is not already running)
npm run api:prototype
# Terminal2
npm run worker:prototype
# Terminal3
$env:VITE_QUOTE_WIZARD='true'
npm --prefix frontend run dev -- --port 4176 --strictPort
```

Run the focused motion checks separately:

```powershell
$env:VITE_QUOTE_WIZARD='true'
npm --prefix frontend run dev -- --port 4176 --strictPort
npx playwright test --config playwright.apple.config.ts
```

The built preview is already available at http://127.0.0.1:4174. New dev sessions may contain no saved selection, so complete/seed the existing journey before reviewing its selection step. Open the homepage explainer, Search, mobile navigation, cookie choices or broker help to review the shared sheet. Keep audit/APPLE_DESIGN_AUDIT.md untracked when reviewing Git status.

## Real-phone/manual checks still required

1. iOS Safari and Android Chrome: hold/cancel buttons, inline links and interactive cards; verify thumb targets and no accidental navigation while scrolling.
2. Grab the sheet while it is opening/closing; slow drag, reversal, fast flick, pointer cancellation, rotation and resize. Check flick momentum and no visual seams on60/120Hz displays.
3. Drag the handle upward past the top; release upward/downward at different speeds; scroll/select long content separately. Confirm no browser gesture conflict.
4. Toggle OS Reduce Motion, Reduce Transparency and Increased Contrast while a sheet is open; repeat with keyboard, VoiceOver/TalkBack and forced colors.
5. Scroll busy photos/text under the glass header; check legibility, frame pacing, zoom and large text. No tactile or hardware performance claim was made.

## Stop condition

The pass is complete locally. Wait for owner review. Do not push unless the owner replies exactly `approved: push`; then publish only `apple-design-pass`. Do not merge or open a PR unless separately requested.
