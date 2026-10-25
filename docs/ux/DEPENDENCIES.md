# Additional dependency decision

Phase13 audit found42 advisories in four pinned Python packages. Updated certifi2026.10.23, Pillow13.0.0 (expanded major range with regression testing), urllib3 2.8.0 and langgraph-checkpoint-postgres3.2.0 with checkpoint4.3.0. Final pinned runtime pip-audit and both npm audits reported zero known advisories. The audit tool ran through uvx; it is not a runtime dependency. No new application dependency for counts/broker preparation. See DEPENDENCY_AUDIT.json.

Phase8 adds phonenumbers (Python port of libphonenumber) because the plan explicitly requires international E.164 parsing/validation. Existing regex checks do not validate country numbering rules; implementing those rules locally is not a small or safe replacement. No new frontend library is required. All transports reuse httpx or Python SMTP. Resolved version is recorded in backend/uv.lock.
