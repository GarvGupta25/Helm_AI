# Light journey refresh and WhatsMCP setup

Updated25 October2026. The design/reference changes preserve every question, option value, consent, hard requirement and deterministic pricing/ranking rule.

## What changed

The plan/dashboard screenshots were caused by an automatic dark-mode rule setting pale inherited text over cards that remained white. Removed that rule, fixed card text at the shared card surface, and made the whole guided experience use light native controls regardless of OS preference. White cards, a warm off-white canvas, subtle teal selection/focus and restrained borders replace the navy page background. Intake topics have a narrower centered reading column and simpler selected/hover states, following the one-topic progression and restrained layout of the Oscar reference. Existing header, question wording, Back/Next, save, optional skips, review, Undo and both intake modes remain.

Regression coverage explicitly checks text/background contrast >=4.5:1 on plan and quotation cards in normal/hover/focus states under dark OS preference, desktop/mobile, then exercises detail, private dashboard and saved form answers. Images in this directory are synthetic only.

## Set up real WhatsMCP later

An ignored `backend/.env` has been created locally for the owner to fill. **Never commit it, put keys in VITE_* or paste the key in chat.** The committed `backend/.env.example` contains the variable names only.

1. Link your sender at https://console.whatsmcp.com, then create its API key and copy the account ID. This implementation uses the documented REST API; installing an MCP client plugin is unnecessary for website sends.
2. In `backend/.env`, fill:

```dotenv
WHATSMCP_API_KEY=your-private-key
WHATSMCP_ACCOUNT_ID=your-linked-sender-account-id
OTP_ALLOWLIST=["+your-approved-international-test-number"]
PUBLIC_QUOTE_ORIGIN=https://your-public-helm-address
OTP_DELIVERY_MODE=whatsmcp
```

Keep the sender and recipient numbers distinct if your account cannot send to itself. The recipient must be entered in E.164 form exactly as in OTP_ALLOWLIST. Use only the operator-approved number during this prototype.

3. Run `uv run --project backend python backend/scripts/whatsmcp_check.py`. It reads only your account list, reports whether the configured sender is live, and sends nothing. It never prints your key, account ID or phone number.
4. The private link needs an **HTTPS URL that opens this same frontend and API from your phone**. A localhost/127.0.0.1 address points at the phone itself and is rejected. Use your own staging hostname or a separately configured development tunnel; no tunnel/deployment or public exposure was created by this change. Ensure that origin is configured with the reverse proxy and allowed origins as appropriate. Keep the prototype disclosure and production guard.
5. Restart the isolated API and worker with explicit messaging permission (stop only their verified task PIDs first):

```powershell
npm run api:prototype
# In a separate terminal, once /health responds:
npm run worker:prototype
```

The normal API now honors the real WhatsMCP configuration. Only the separate automated test server forces console. The public verification page never offers local codes, even against that test server. Missing keys disable verification with an unavailable notice; no provider key is needed to inspect the other prototype pages.

6. Use the website normally: review/select plans, choose WhatsApp, enter the approved number and allow the verification code. Enter the code from your WhatsApp. On access choice, select24/48h and tick **Send the private access link and quotation updates through my verified channel** before creating the link. That explicit request sends the access link promptly; later quotation updates/reminders respect quiet hours. Keep sharing/notification consent unticked unless you want messages.

The API checks the recipient allowlist, stores only encrypted contact/hashed OTP material, preserves10-minute expiry/five attempts/cooldown/limits, and never falls back to pretending a real send worked. Responses distinguish sent, accepted-but-queued, quota, disconnected sender, credentials and failed delivery. A202 queued response is never automatically retried. Network timeouts are ambiguous; check WhatsApp before requesting another code. Link status appears on the access page. All quotations remain synthetic.

## Free plan and official Business distinction

The [current WhatsMCP plans](https://whatsmcp.com/plans) list Personal Free with30 messages/day,10/hour, REST access and29/46 MCP tools. The quota is per connected sender and shared with other clients: one OTP and one link use at least two messages; optional updates/reminders use more. Provider429 errors remain visible. No fixed quota promise is made by Helm.

The free Personal plan links a number as a device; the provider says this route falls outside WhatsApp's terms and numbers can be restricted. Its official Business/Cloud API plans are separate. See [provider explanation](https://whatsmcp.com/). Personal mode uses text messages. An official Business account can reuse WHATSAPP_AUTH_TEMPLATE/WHATSAPP_UTILITY_TEMPLATE and WHATSAPP_TEMPLATE_LANGUAGE for approved templates; outside its24h window a template is required. Check account/template support with the provider; no paid plan or terms were accepted here.

Primary contract checked: [REST documentation](https://whatsmcp.com/docs/rest) and https://api.whatsmcp.com/openapi.json. The fixed HTTPS send endpoint is `/v1/accounts/{account_id}/messages`, with server-side X-API-Key and `to`/`text` or approved template variables.

## Verification and limits

Actual command results are recorded below after completion. Tests use mocked WhatsMCP HTTP responses and the isolated local console service. **No live WhatsApp message was sent or received:** the owner chose to paste their key later. Real delivery, physical devices and hosted routing remain unverified until those settings exist. No production launch, legal/compliance clearance or paid subscription is implied.

### Actual verification results

- Full backend:513 passed,1 skipped in103.36s; existing Starlette/AnyIO deprecation warning only. Focused transport/verification/access/notification run:15 passed in4.08s. Mocked HTTP tests cover the documented endpoint/header/payload, OTP verification after queued acceptance, private link dispatch, idempotency, no local OTP reveal in external mode, allowlist/origin checks, templates, timeout,401/403/409/429/500/refused responses. No real message was sent.
- Frontend check, scoped lint and16 unit tests passed; final flag-on demo build passed7.18s. Production guard still intentionally exits1.
- Wizard browser batches:9 passed1.2min (detail, mandatory, plans, contrast);9 passed1.1min (access, mandatory, contrast and verification);9 passed1.2min (broker, dashboard, hardening, plans and toolbar chat); final contrast/interaction rerun2 passed34.2s after spacing changes. These cover18 unique wizard tests, with targeted reruns following UI fixes. Serious/critical axe checks passed on exercised pages. Actual normal/hover/focus card contrast is asserted >=4.5:1 under dark OS preference at1440/375px; form Next clickability, toolbar chat open/close and preserved saved values are checked.
- Screenshot review exposed the floating broker overlapping mobile Next. It is now docked in sticky navigation; toolbar Ask Helm opens the same assistant without a launcher over the choices. Other public pages retain their normal launcher. See light-plan-card.png, light-quotation-card.png and light-mobile-form.png.
- The read-only setup check correctly reports missing credentials (expected exit1); backend/.env is confirmed ignored. Secret-pattern and diff checks ran before commit. Physical phones, manual screen readers and actual public routing/provider delivery remain unverified.
- Full UK/public/chat/member/legacy browser suite:27 passed in1.7min against the rebuilt preview. This also verifies the normal public launcher remains functional outside the guided journey.
- For the first real-delivery test, start a fresh private comparison. Existing console-verified cases cannot be renewed as a different real contact; the original-contact binding is preserved.


## Real verification correction
Normal verification asks for an actual WhatsApp number and never renders the former local inbox, reveal button, fictional-number prompt or simulation banner. Country code, consent, six-box paste/keyboard support, countdown, attempts and verified private access remain. Email is offered only when configured. Readiness is checked before allowing Send; missing sender setup is an honest unavailable state. A transport change invalidates old console challenges.

Normal startup: `npm run api:prototype` and `npm run worker:prototype`; the API uses the same isolated SQLite/key setup, with configured real transport instead of the test-only console override. `backend/.env` is currently set to whatsmcp, with key/sender/recipient/origin still blank. The sender cannot deliver until those fields are completed. No real message is claimed. Stop the normal API before browser regression suites that require the isolated console test server.

### Actual verification correction results
Full backend515 passed/1 skipped; focused14 passed; frontend16 unit tests, TypeScript, scoped lint, Ruff and demo build passed. Final browser8 passed plus1 smoke against the actual preview. The current normal API reports mode=whatsmcp and readiness=false because credentials remain blank. The normal UI has no local-code reveal path. Production guard stays closed. No actual message delivery was exercised; configured-sender UI cases use explicit fixtures and the REST transport is covered by mocked backend integration tests.
