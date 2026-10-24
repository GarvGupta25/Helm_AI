import { useState } from 'react';
import { journey, money, type Profile } from './api';
import type { Comparison } from './Recommendations';
import DemoInbox from './DemoInbox';

export type CaseState = { id: string; state: string; version: number; profile_version: number; requests: { id: string; insurer_id: string; status: string }[]; notice: string };
type Mail = { id: string; kind: string; contact_id: string; content: { code?: string; text?: string; url?: string; notice?: string } };
export default function QuoteRequest({ result, selected, profile }: { result: Comparison; selected: string[]; profile: Profile }) {
  const [channel, setChannel] = useState('email');
  const [destination, setDestination] = useState('');
  const [contactId, setContactId] = useState('');
  const [contacts, setContacts] = useState<{ id: string; channel: string }[]>([]);
  const [code, setCode] = useState('');
  const [inbox, setInbox] = useState<Mail[]>([]);
  const [insurerConsent, setInsurerConsent] = useState(false);
  const [brokerConsent, setBrokerConsent] = useState(false);
  const [notify, setNotify] = useState(false);
  const [ack, setAck] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [caseState, setCaseState] = useState<CaseState>();
  const [quietStart, setQuietStart] = useState(22);
  const [quietEnd, setQuietEnd] = useState(8);
  async function perform(action: () => Promise<void>) { setBusy(true); setNotice(''); try { await action(); } catch (e) { setNotice(e instanceof Error ? e.message : 'Please try again.'); } finally { setBusy(false); } }
  const items = result.items.filter(i => selected.includes(i.id));
  async function submit() {
    const consents: string[] = [];
    async function consent(purpose: string, recipients: string[]) { const c = await journey<{ id: string }>('/consents', { purpose, recipients, accepted: true, wording_version: 'journey-sharing-v1' }); consents.push(c.id); }
    await consent('insurer_share', [...new Set(items.map(i => i.plan.insurer_id))].sort());
    if (brokerConsent) await consent('broker_share', ['helm-demo-broker']);
    if (notify) for (const c of contacts) await consent(`notify_${c.channel}`, [c.id]);
    const data = await journey<CaseState>('/quote-requests', { run_id: result.run_id, expected_version: result.profile_version, plan_ids: selected,
      contact_ids: contacts.map(c => c.id), consent_ids: consents, channels: notify ? ['dashboard', ...contacts.map(c => c.channel)] : ['dashboard'], quiet_start: quietStart, quiet_end: quietEnd, time_zone: 'Europe/London', demo_acknowledged: true });
    setCaseState(data);
    try { sessionStorage.setItem('helm-journey-case', data.id); } catch { /* Optional local bookmark. */ }
  }
  return <section className="j-panel" aria-label="Review and request simulated quotations"><h3>Review and request simulated quotations</h3><p>Profile version {result.profile_version}. Nothing is sent to a real insurer. The demo keeps a consented case snapshot for up to seven days; quotations expire separately.</p>{items.map(i => <p key={i.id}><strong>{i.plan.name}</strong> · {money(i.quote.monthly_pence)}/month · fictional insurer {i.plan.insurer_id}</p>)}<details><summary>Review the exact fictional profile to be shared</summary><pre>{JSON.stringify(profile, null, 2)}</pre></details>
    {!caseState && <><h4>Verify a demo contact</h4><p>Use a fictional .test email or fictional international number. A code appears only in your private demo inbox. This does not prove ownership of a real email or WhatsApp account.</p><div className="j-toolbar"><label className="j-field">Contact channel<select value={channel} onChange={e => setChannel(e.target.value)}><option value="email">Email</option><option value="whatsapp">WhatsApp</option></select></label><label className="j-field">Fictional contact<input value={destination} onChange={e => setDestination(e.target.value)} placeholder={channel === 'email' ? 'visitor@example.test' : '+999700000001'} maxLength={180}/></label></div><label className="j-check"><input type="checkbox" checked={ack} onChange={e => setAck(e.target.checked)}/> I understand that verification, insurer requests and delivery are simulations and will use fictional details.</label><button disabled={busy || !ack || !destination || contacts.some(c => c.channel === channel)} onClick={() => void perform(async () => { const data = await journey<{ contact_id: string }>('/contacts/challenges', { channel, destination, demo_acknowledged: true }); setContactId(data.contact_id); setInbox(await journey<Mail[]>('/demo/inbox')); })}>Get demo verification code</button>{contactId && <><label className="j-field">One-time demo code<input inputMode="numeric" autoComplete="one-time-code" value={code} onChange={e => setCode(e.target.value)} maxLength={6}/></label><button disabled={busy || code.length !== 6} onClick={() => void perform(async () => { await journey('/contacts/verify', { contact_id: contactId, code }); setContacts(old => [...old.filter(c => c.channel !== channel), { id: contactId, channel }]); setContactId(''); setCode(''); setInbox([]); setNotice('Contact verified in this simulation. You can add the other channel if needed.'); })}>Verify demo contact</button></>}{inbox.length > 0 && <details open><summary>Private demo inbox</summary>{inbox.filter(m => m.content.code).map(m => <p key={m.id}>One-time simulation code: <strong>{m.content.code}</strong></p>)}</details>}{contacts.map(c => <p key={c.id}>{c.channel} verified in demo <button onClick={() => setContacts(old => old.filter(v => v.id !== c.id))}>Remove {c.channel} contact</button></p>)}<hr/><label className="j-check"><input type="checkbox" checked={insurerConsent} onChange={e => setInsurerConsent(e.target.checked)}/> I explicitly consent to share this reviewed fictional profile and selected plans with these named demo insurers: {[...new Set(items.map(i => i.plan.insurer_id))].join(', ')}.</label><label className="j-check"><input type="checkbox" checked={brokerConsent} onChange={e => setBrokerConsent(e.target.checked)}/> Also share my case, contact and saved questions with the Helm demo broker workspace, after assignment. I can withdraw this consent.</label><label className="j-check"><input type="checkbox" checked={notify} onChange={e => setNotify(e.target.checked)}/> Send simulated quotation updates through my verified channels. Otherwise use dashboard only.</label><div className="j-toolbar"><label className="j-field">Quiet hours start (Europe/London)<input type="number" min="0" max="23" value={quietStart} onChange={e => setQuietStart(Number(e.target.value))}/></label><label className="j-field">Quiet hours end (Europe/London)<input type="number" min="0" max="23" value={quietEnd} onChange={e => setQuietEnd(Number(e.target.value))}/></label></div><button disabled={busy || !contacts.length || !insurerConsent || !ack || !items.length} onClick={() => void perform(submit)}>Request simulated quotations</button></>}
    {caseState && <div role="status"><h4>Your demo case is saved</h4><p>{caseState.notice}</p><p>Case {caseState.id}</p><DemoInbox caseId={caseState.id}/>{caseState.requests.map(r => <p key={r.id}>{r.insurer_id}: {r.status}</p>)}<button disabled={busy} onClick={() => void perform(async () => setCaseState(await journey<CaseState>(`/cases/${caseState.id}`)))}>Refresh request status</button></div>}{notice && <p role="status">{notice}</p>}
  </section>;
}
