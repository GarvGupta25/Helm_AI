# Funnel measurement — operator report

Counts are disabled by default. To enable, migrate to head, set server `JOURNEY_FUNNEL_ENABLED=true` and frontend `VITE_FUNNEL_ANALYTICS=true`, then rebuild. Each visitor must independently allow Analytics. Changing Cookie settings to reject Analytics stops future counts. No third-party service receives events.

`uv run --project backend python backend/scripts/funnel_report.py` reads daily totals using the operator's database configuration. It exports fixed event, step, mode, choice and count only. No public reporting endpoint exists. Retention worker deletes rows older than 30 days.

Events: step_view, step_complete, mode_chosen, show_plans (checkpoint/optional/review), plans_viewed, selection_complete, otp_started, otp_success, link_choice (24/48), dashboard_open, broker_requested. Client suppresses duplicate categories during one application load. Navigation skips count as progression, not evidence that an answer was supplied. Guided and manual completion share their step categories.

## Report template

Period (UTC dates): ___  Analytics enabled since: ___  Sample caveats: ___

| Step | Views | Progressions | Apparent drop-off: max(0, 1-progressions/views) | Observation / proposed change |
|---|---:|---:|---:|---|
| people | | | | |
| region | | | | |
| start-date | | | | |
| budget / excess / hospitals | | | | |
| benefits groups | | | | |
| optional steps | | | | |

Mode-choice totals: manual ___ chat ___. Show-plans totals: checkpoint ___ optional ___ review ___. Plans viewed ___ selections ___ verification starts ___ successes ___ link24 ___ link48 ___ dashboard opens ___ broker requests ___.

These are consented event totals, **not unique visitors or a joined conversion funnel**. Refreshes, resumed sessions, prior consent rejection, retries, backtracking and ad blockers distort ratios. OTP success/start is a proxy, not a verified ownership success rate. No visitor/session/account IDs or answers exist to join them. Do not infer a person's health, behaviour, or outcome from this report. Application anti-abuse IP buckets exist transiently in memory for one hour; IPs are not written into the counts table. Deployment access-log retention needs its own review.
