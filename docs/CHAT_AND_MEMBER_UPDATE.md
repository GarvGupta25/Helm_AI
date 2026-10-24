# Chat feedback, uploads and member accounts

Delivered for the 24 October 2026 request in the shared [Helm AI repository](https://github.com/GarvGupta25/Helm_AI). Development author: **Utkarsh Raj**. All insurance/policy examples remain synthetic.

## Delivered interface

- The attachment area now has a compact document header, distinct PDF/photo/camera tiles, visible file limits, a separate consent row and a quieter privacy explanation. PDF is visually highlighted. Keyboard focus, disabled states, contrast and mobile/dark layouts use the existing navy/white/teal chat tokens. Temporary-processing consent and existing file validation remain required.
- Each completed assistant answer has copy, read aloud/stop, helpful, not helpful, regenerate on the latest answer, and report-issue actions. A negative vote can include optional structured feedback. The report form supports incorrect, unclear, safety, technical and other categories, with a reference after saving. Conversation options also offers a general issue report.
- Read aloud uses available browser speech-synthesis voices, prefers a local English voice when present, and starts only after a click. Switching answers, stopping, closing or clearing the chat cancels speech. Unsupported browsers show the disabled control/fallback. The modern widget is enabled by default in both development and built previews; `VITE_NEXT_CHAT_UI=false` remains an explicit legacy rollback. No new speech provider or dependency was added; actual voice availability depends on the browser/device.
- Arabic translation/pickers were removed from active public chat and guided intake, and the header no longer offers a language menu. Active guidance/transcription APIs accept English. Input text may still contain ordinary Unicode; old archive files/historical reports were not rewritten.
- The account menu now clearly offers **Create an account** and **Member log in**. Professional access is preserved separately. The local prototype has matching registration/login pages with name, email, password, password visibility and explicit demo-account shortcuts.
- New accounts land on an onboarding page with no policies and profile/comparison guidance. Policyholders land on a dashboard with saved policies, renewal information, premium, excess, benefits and exclusions. The distinction comes from the authenticated server-owned policy records, not a browser query flag.

## Open the running demo

| Entry | URL |
| --- | --- |
| Website and chat | [127.0.0.1:4174](http://127.0.0.1:4174/) |
| Create an account | [/signup](http://127.0.0.1:4174/signup) |
| Member sign-in / demo shortcuts | [/login](http://127.0.0.1:4174/login) |
| Authenticated landing | [/member](http://127.0.0.1:4174/member) |

The sign-in screen has two buttons that use the normal password-login endpoint. These are real saved prototype accounts, not browser-only page switches:

| Example | Name | Email | Demo password |
| --- | --- | --- | --- |
| New member, no policies | Alex Morgan | `new.member@example.test` | `HelmDemo!2026` |
| Policyholder, one fictional policy | Jamie Taylor | `policy.member@example.test` | `HelmDemo!2026` |

These public fixture credentials are only for the explicitly enabled local synthetic service. They do not grant broker/provider access or establish real cover. Seeding is idempotent and does not overwrite an existing account/password. Registration also supports a new fictional account, which survives page reload/API restart in the local database.

## Account storage and auth boundaries

The isolated API script enables `MEMBER_DEMO_AUTH=true` in development and creates the new `member_demo_account`, `member_demo_session` and `member_demo_policy` tables in `.runtime/uk-e2e.db`. Additive Alembic migration `0006_member_demo` is included; it was applied to the scratch database. Existing environments should use their normal reviewed migration process.

Names/email and policy snapshots use the existing encrypted storage type. Email lookup uses a keyed digest. Passwords use salted scrypt (`n=32768`, `r=8`, `p=1`) and are never stored in plain text or exposed by the account API. Sessions use random tokens, store only their digests, expire after 12 hours and use HttpOnly/SameSite=Strict cookies (Secure over HTTPS). Logout revokes the session. Registration/login keep independent IP rate limits, validate their inputs and reject unrelated request origins.

The local service is member-only and requires the explicit setting plus a development/test environment and stable encryption key. It returns unavailable outside those environments. It cannot authenticate historical customer APIs, broker APIs or provider APIs. Existing Supabase bearer-token verification and administrator-controlled professional roles are unchanged. With the demo service disabled, `/login` and `/signup` use the existing Supabase flow; full name is passed into account metadata. Local email verification and password recovery are not implemented; no mail is sent.

## Separate chatbot feedback database

Default/local prototype file: **`.runtime/chatbot-feedback.db`**. It is physically separate from the member/journey database and has its own SQLAlchemy metadata containing only `chatbot_feedback`.

Each record has a UUID reference, hashed random browser-tab identifier, response UUID, vote/report type, rating, category, status and timestamps. Submitted text is encrypted. There is one current vote/report per response and tab; changing a vote updates that record. Optional details are bounded to 1,500 characters. A response excerpt (up to 6,000 characters) is saved only when the user explicitly checks the include-answer box. Full conversation history, original user prompt, account identity/email, uploads and audio are not automatically attached. No feedback is used for model training by this code.

Configure another independent database with server-only `CHATBOT_FEEDBACK_DATABASE_URL`. A stable `RESEARCH_STATE_KEY` is required for encrypted persistence; the isolated demo reuses its existing `.runtime/research-test.key`. Keep the key with protected backups, not in Git or a `VITE_*` setting. The database/key files remain ignored.

The feedback table initializes idempotently in its dedicated database. Votes/reports retain the existing limit of ten mutations per IP per hour. There is no public feedback-list/export endpoint. Local operator commands:

```powershell
# Counts by feedback/report, rating and category; does not print submitted text
uv run --project backend python backend/scripts/chatbot_feedback_store.py

# Explicit private export of up to 5,000 submitted records; refuses to overwrite a file
uv run --project backend python backend/scripts/chatbot_feedback_store.py --export .runtime/chatbot-feedback-export.json

# Delete expired records
uv run --project backend python backend/scripts/chatbot_feedback_store.py --purge-expired
```

Retention is 90 days from the latest update. Expiry cleanup runs on submissions and every ten minutes in the local demo worker. Keep that worker active for scheduled cleanup. Exported copies need their own appropriate handling/deletion; the store cannot erase an operator's separate export. The privacy page describes these actual storage boundaries.

## Run locally

Use the existing setup in [README](../README.md) and [journey runbook](roadmap/JOURNEY_RUNBOOK.md). The isolated API seeds the two member fixtures; the worker processes quotation jobs and feedback cleanup. Separate terminals:

```powershell
uv run --project backend python backend/scripts/uk_test_server.py
uv run --project backend python backend/scripts/journey_worker.py
```

```powershell
$env:VITE_NEXT_CHAT_UI='true'
npm run build
npm --prefix frontend run preview
```

The two Python commands are separate long-running processes. The build serves the latest frontend at port 4174. The preview, API and worker are left running after delivery.

## Verification

Results measured for this change:

| Check | Result |
| --- | --- |
| Full backend suite, isolated `DATABASE_URL=sqlite://`, provider key disabled | **484 passed, 1 skipped**, 39.22 seconds; one existing dependency deprecation warning |
| Skipped backend check | Existing PostgreSQL-specific database-role test; no PostgreSQL concurrency claim |
| Additional account environment/role checks after tightening demo gating | **1 passed**; production/prod/staging denied |
| Frontend unit tests | **12 passed**, including start/switch/stop/close and unsupported-browser read-aloud checks |
| TypeScript, scoped ESLint and demo build | Passed; existing Home import/chunk warning remains |
| Public/journey/member/chat browser suite | **27 passed**, including actual local registration/relogin, both database-backed demo landing pages, desktop/mobile scoped axe, upload consent/dark mode, persisted feedback/issue reports, speech controls with a browser fixture, and existing scroll/composer/journey regressions |
| Legacy customer account/browser suite | **9 passed**, including broker/provider role guidance and customer marketplace/claims regressions |
| Final default-build smoke check after metadata/footer/default-widget polish | **7 passed** — member flows, chat feedback/upload/read controls and scroll/composer checks |
| Production build | Expected failure: existing live-release blockers remain; guard not bypassed |
| Active source scan | No Arabic picker/translation strings remain in frontend source |

The separate feedback-store summary was inspected after the browser tests and showed saved vote/report rows. Unit checks also verify storage encryption, duplicate updates, explicit answer-sharing, expiry and absence from the main database metadata. Account checks cover hashing, normalization, session expiry/logout, duplicate registration, policy ownership, foreign-origin rejection and professional-auth separation.

Screenshots retained locally: `.runtime/member-new-preview.png`, `.runtime/member-policyholder-preview.png`, `.runtime/member-new-desktop.png`, `.runtime/member-policyholder-desktop.png`, `.runtime/member-policyholder-mobile.png`, `.runtime/chat-upload-modern-mobile.png`, and `.runtime/chat-response-actions.png`, and `.runtime/chat-upload-preview.png`. Browser traces/report are under `.runtime/member-chat-full-results` and `.runtime/member-chat-final-playwright.json`.

No physical mobile microphone/speech device, real account email delivery, production database or live insurer/payment was exercised. Synthetic policies and local demo accounts remain clearly labeled. No new dependency was added.
