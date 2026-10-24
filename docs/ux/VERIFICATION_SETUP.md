# Verification transport setup and limits

Updated25 October2026. The isolated `uk_test_server.py` explicitly forces OTP_DELIVERY_MODE=console, so automated tests never send to people even if a developer has provider secrets configured elsewhere.

## Implemented transports

ConsoleProvider keeps a code only in a bounded10-minute process-memory inbox, accessible through the owning session in development/test. It prints a static masked notice. It does not prove ownership. WhatsAppCloudProvider sends an approved authentication template through graph.facebook.com only. EmailProvider uses authenticated SMTP over TLS (SMTP_SSL). Both network transports require an exact operator allowlist. No unofficial WhatsApp bridge or public credential is used.

## Official sandbox prerequisites

1. Set up and verify the WhatsApp Business Account and register its sending phone number in the official provider account. Get an approved AUTHENTICATION template with copy-code button and its exact language/locale. An approved business account/template is external configuration, not something this code can assert.
2. On a reviewed non-production backend with a stable RESEARCH_STATE_KEY, configure OTP_DELIVERY_MODE=whatsapp_sandbox, OTP_ALLOWLIST as a JSON array of E.164 test recipients, WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_GRAPH_VERSION (the explicitly supported version for the account), WHATSAPP_AUTH_TEMPLATE and WHATSAPP_TEMPLATE_LANGUAGE. Keep all secrets server-side, never VITE_* or Git.
3. For email fallback set SMTP_HOST, SMTP_PORT(default465), SMTP_USER, SMTP_PASSWORD and SMTP_FROM. The selected email must also be in OTP_ALLOWLIST. OTP_DELIVERY_MODE=email_sandbox restricts delivery to that channel.
4. Apply additive migration0007_wizard_otp through the normal reviewed migration process. The isolated scratch API creates its table idempotently without touching the configured customer database.
5. Exercise only approved test recipients and confirm actual receipt, expiry, cooldown, five-guess lockout, old-code replacement, network failures and webhook/operations behavior before claiming a working live integration. Current execution used mocked transports and console only. No real WhatsApp/email was sent.

## Security and privacy

Each six-digit CSPRNG code is bound to a random contact id and stored as a keyed HMAC. Only the encrypted destination, code hash, ten-minute expiry, bounded attempts, selection fingerprint and versioned opt-in are persisted. Codes are never logged or persisted in the new flow. Per-number and per-session rolling3/hour windows are encrypted, persisted and locked, with60-second resend cooldown. Existing10/IP/hour limiter remains. The number window identifies the only active challenge; older challenges fail. The legacy verify endpoint cannot accept new-flow contacts. Wrong guesses commit attempt counts. Success consumes the code and produces an HttpOnly/SameSite session cookie.

Phone validation uses phonenumbers9.0.41 and canonical E.164. Optional marketing/reminders are not inferred from verification permission. Counters expire after2 idle hours; contact/case retention remains in the existing7-day worker policy. Local codes disappear on restart; request a new code after cooldown. Operational PostgreSQL concurrency, distributed IP limiting and actual provider delivery remain unverified.

The new flow uses /api/journey/verify/start, /check, /status and owning-session-only /demo-code, rather than duplicating the older research API. Selection and profile-version checks are mandatory.

## Reference checked while implementing

The official Meta Postman collection identifies the authentication-template API: https://www.postman.com/meta/whatsapp-business-platform/request/6vkv46u/create-authentication-template-w-otp-copy-code-button . The primary AWS Messaging example documents the compatible body/button parameters: https://aws.amazon.com/blogs/messaging-and-targeting/send-whatsapp-business-messages-with-aws-end-user-messaging-social/ . Meta documentation returned429 during this check; live account/version/template acceptance still requires provider-side verification. No current Graph version was guessed.

For reviewed link/quote notifications, configure WHATSAPP_UTILITY_TEMPLATE with one body URL parameter and PUBLIC_QUOTE_ORIGIN as an HTTPS origin, then start journey_worker.py --allow-configured-sandbox explicitly. The default worker forces console and never sends externally. Existing-condition/profile data and AI draft text are never sent by these fixed utility templates. Cross-device recovery requires the configured transport; local demo recovery needs its private mailbox cookie.
