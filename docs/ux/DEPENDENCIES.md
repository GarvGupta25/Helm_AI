# Additional dependency decision

Phase8 adds phonenumbers (Python port of libphonenumber) because the plan explicitly requires international E.164 parsing/validation. Existing regex checks do not validate country numbering rules; implementing those rules locally is not a small or safe replacement. No new frontend library is required. All transports reuse httpx or Python SMTP. Resolved version is recorded in backend/uv.lock.
