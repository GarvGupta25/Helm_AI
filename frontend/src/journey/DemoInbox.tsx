import { useState } from 'react';
import { journey } from './api';

type Mail = { id: string; kind: string; content: { code?: string; url?: string; text?: string; notice?: string; expires_at?: string } };
export default function DemoInbox({ caseId }: { caseId?: string }) {
  const [messages, setMessages] = useState<Mail[]>([]);
  const [hours, setHours] = useState('24');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  async function load(create = false) { setBusy(true); setNotice(''); try { if (create && caseId) await journey('/access-links', { case_id: caseId, hours: Number(hours) }); setMessages(await journey<Mail[]>('/demo/inbox')); } catch (e) { setNotice(e instanceof Error ? e.message : 'Inbox unavailable.'); } finally { setBusy(false); } }
  return <section className="j-panel" aria-label="Private simulated delivery inbox"><h3>Your private demo inbox</h3><p>No real email or WhatsApp messages are sent. Links here grant access to your fictional case; do not share them.</p>{caseId && <><label className="j-field">Dashboard link validity<select value={hours} onChange={e => setHours(e.target.value)}><option value="24">24 hours</option><option value="48">48 hours</option></select></label><button disabled={busy} onClick={() => void load(true)}>Create private dashboard link</button></>}<button disabled={busy} onClick={() => void load()}>Refresh private inbox</button>{messages.map(m => <article key={m.id}><h4>{m.kind.replaceAll('_', ' ')}</h4><p>{m.content.text || m.content.notice}</p>{m.content.code && <p>One-time simulation code: <strong>{m.content.code}</strong></p>}{m.content.url?.startsWith('/quote-dashboard#') && <a className="uk-button secondary" referrerPolicy="no-referrer" href={m.content.url}>Open private quote dashboard</a>}{m.content.expires_at && <p>Expires {new Date(m.content.expires_at).toLocaleString()}</p>}</article>)}{notice && <p role="status">{notice}</p>}</section>;
}
