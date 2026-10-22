# Security review — engineering checklist, not an ASVS certification

Implemented: no new client-side secrets; public quotes use random capabilities in headers (not URLs); seven-day access expiry; frozen server prices; explicit consent booleans; zero real payment; idempotent confirmation with row lock on Postgres; raw public messages never stored or sent to inference; bounded assistant messages and per-process rate buckets; forwarded headers cannot directly bypass the assistant limit; external-link confirmation; Radix modal focus management; no optional scripts.

Outstanding ASVS L2 work: production threat model; distributed API/quote abuse limits; gateway body-size limits; static-host CSP and security-header verification; key management; dependency/SBOM policy; independent authorisation/IDOR testing of all historical routes; production storage/log redaction; MFA and privileged access; complete audit retention evidence; incident response exercise; CSRF review for eventual cookie-based endpoints; payment processor assessment; carrier IPID integrity; supported browser/device verification.

The backend regression suite is evidence for tested behaviour, not proof of ASVS L2 compliance. Run `npm audit` for both packages and dependency review in CI. Never commit `.env`, customer exports or production credentials. The assistant has not scanned private user folders or printed secrets.
