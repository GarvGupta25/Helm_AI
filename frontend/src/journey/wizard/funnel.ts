type Event = 'step_view'|'step_complete'|'mode_chosen'|'show_plans'|'plans_viewed'|'selection_complete'|'otp_started'|'otp_success'|'link_choice'|'dashboard_open'|'broker_requested';
type Mode = 'manual'|'chat'|'';
const sent = new Set<string>();
export function track(event: Event, step: string, mode: Mode = '', choice: ''|'24'|'48'|'checkpoint'|'optional'|'review' = '') {
  if (import.meta.env.VITE_FUNNEL_ANALYTICS !== 'true') return;
  try { if (JSON.parse(localStorage.getItem('helm-cookie-consent-v1') || '{}').analytics !== true) return; } catch { return; }
  const key = [event, step, mode, choice].join(':');
  if (sent.has(key)) return;
  sent.add(key);
  // No capabilities, credentials, answers, URLs or account identifiers accompany counts.
  void fetch('/api/journey/funnel', { method: 'POST', credentials: 'omit', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event, step, mode, choice, analytics_consent: true }) }).catch(() => {});
}
