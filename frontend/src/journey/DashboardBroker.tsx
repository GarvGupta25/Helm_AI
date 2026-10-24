import { useState } from 'react';
import { journey } from './api';

export default function DashboardBroker({ version, refresh }: { version: number; refresh: () => Promise<void> }) {
  const [consent, setConsent] = useState(false);
  const [text, setText] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  async function perform(action: () => Promise<void>) { setBusy(true); setNotice(''); try { await action(); await refresh(); } catch (e) { setNotice(e instanceof Error ? e.message : 'Please retry.'); } finally { setBusy(false); } }
  return <section className="j-panel"><h2>Talk to a broker</h2><p>Share this fictional profile, verified contact, quotations and saved questions with your assigned Helm demo broker. You can withdraw sharing at any time.</p><label className="j-check"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)}/> I explicitly consent to this broker sharing.</label><button disabled={busy || !consent} onClick={() => void perform(async () => { const r = await journey<{ notice: string }>('/dashboard/broker-handoff', {}); setNotice(r.notice); })}>Contact a broker about this case</button><label className="j-field">Message your broker<textarea value={text} onChange={e => setText(e.target.value)} maxLength={3000} rows={3}/></label><button disabled={busy || !text.trim()} onClick={() => void perform(async () => { await journey('/dashboard/messages', { expected_version: version, text }); setText(''); setNotice('Message saved to your private demo thread.'); })}>Send demo message</button><button disabled={busy} onClick={() => void perform(async () => { await journey('/dashboard/broker-sharing/withdraw', {}); setNotice('Broker sharing withdrawn. Broker access has ended.'); })}>Withdraw broker sharing</button>{notice && <p role="status">{notice}</p>}</section>;
}
