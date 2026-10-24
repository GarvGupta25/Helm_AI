import { useState } from 'react';
import { journey, type IntakeState } from './api';
import DemoInbox from './DemoInbox';

export default function BrokerHandoff({ prepare }: { prepare: () => Promise<IntakeState> }) {
  const [open, setOpen] = useState(false);
  const [destination, setDestination] = useState('');
  const [contactId, setContactId] = useState('');
  const [code, setCode] = useState('');
  const [ack, setAck] = useState(false);
  const [consent, setConsent] = useState(false);
  const [verified, setVerified] = useState(false);
  const [caseId, setCaseId] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  async function perform(action: () => Promise<void>) { setBusy(true); setNotice(''); try { await action(); } catch (e) { setNotice(e instanceof Error ? e.message : 'Please retry.'); } finally { setBusy(false); } }
  return <section className="j-panel"><button onClick={() => setOpen(!open)} aria-expanded={open}>Contact a broker</button>{open && <><h2>A human can help at any point.</h2><p>Review the shared profile above. Missing answers are welcome. Use fictional details; nothing is sent externally.</p>{!caseId ? <><label className="j-field">Fictional broker contact email<input type="email" value={destination} onChange={e => setDestination(e.target.value)} placeholder="visitor@example.test" maxLength={180}/></label><label className="j-check"><input type="checkbox" checked={ack} onChange={e => setAck(e.target.checked)}/> I understand this uses simulated verification and fictional information.</label><button disabled={busy || !ack || !destination || verified} onClick={() => void perform(async () => { const r = await journey<{ contact_id: string }>('/contacts/challenges', { channel: 'email', destination, demo_acknowledged: true }); setContactId(r.contact_id); })}>Get broker contact code</button>{contactId && !verified && <><DemoInbox/><label className="j-field">Broker contact one-time code<input inputMode="numeric" value={code} onChange={e => setCode(e.target.value)} maxLength={6}/></label><button disabled={busy || code.length !== 6} onClick={() => void perform(async () => { await journey('/contacts/verify', { contact_id: contactId, code }); setVerified(true); })}>Verify broker contact</button></>}<label className="j-check"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)}/> I explicitly consent to share this reviewed fictional profile, verified contact and saved questions with the assigned Helm demo broker. I can withdraw sharing.</label><button disabled={busy || !verified || !consent} onClick={() => void perform(async () => { const profile = await prepare(); const c = await journey<{ id: string }>('/consents', { purpose: 'broker_share', recipients: ['helm-demo-broker'], accepted: true, wording_version: 'journey-sharing-v1' }); const result = await journey<{ id: string; broker_assigned: boolean }>('/broker-handoff', { expected_version: profile.version, contact_id: contactId, consent_id: c.id, demo_acknowledged: true }); setCaseId(result.id); try { sessionStorage.setItem('helm-journey-case', result.id); } catch { /* Optional bookmark. */ } setNotice(result.broker_assigned ? 'Your case is shared with the assigned demo broker.' : 'Your private case is saved, pending administrator assignment.'); })}>Confirm profile and request broker help</button></> : <DemoInbox caseId={caseId}/>}</>}{notice && <p role="status">{notice}</p>}</section>;
}
