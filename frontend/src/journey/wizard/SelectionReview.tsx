import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LoaderCircle, Pencil } from 'lucide-react';
import { journey, money, type Profile } from '../api';
import type { Comparison, PlanItem } from '../Recommendations';
import { ProfileSummary } from './ProfileSummary';
import { MustHaves } from './Checkout';
import { hospitalName, planName, profileHeadline, readable, wholeMoney } from './checkoutPresentation';
import { pathFor } from './steps';
import BrokerContact from './BrokerContact';

export type SelectionReceipt = { reference: string; run_id: string; profile_version: number; plan_ids: string[]; insurer_consent_id: string; broker_consent_id?: string | null; notice: string };

function PlanSummaryPanel({ item }: { item: PlanItem }) {
  return <article className="flow-plan"><h2 className="flow-plan-title">{planName(item.plan.name)}</h2>
    <p className="flow-premium">{money(item.quote.monthly_pence)}<small> /month</small></p><p className="flow-tax">Including assumed tax. Demo pricing.</p>
    <dl><div><dt>Excess</dt><dd>{wholeMoney(item.plan.excess_pence)}</dd></div><div><dt>Insurer</dt><dd>{item.plan.insurer_id.toUpperCase()} (demo)</dd></div><div><dt>Hospital list</dt><dd>{hospitalName(item.plan.network)}</dd></div></dl>
    <details><summary>Plan details</summary><p>Catalogue name: {item.plan.name}. Version: {item.plan.version}.</p><p>Underwriting: {readable(item.plan.underwriting)}. Existing conditions: {readable(item.plan.pre_existing)}.</p><Link to={'/get-cover/plans/' + encodeURIComponent(item.id)}>Review details</Link></details>
  </article>;
}

export default function SelectionReview({ result, selected, profile }: { result: Comparison; selected: string[]; profile: Profile }) {
  const [insurer, setInsurer] = useState(false); const [broker, setBroker] = useState(false);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [consentError, setConsentError] = useState(false);
  const [receipt, setReceipt] = useState<SelectionReceipt>(); const insurerInput = useRef<HTMLInputElement>(null); const navigate = useNavigate();
  const items = result.items.filter(item => selected.includes(item.id)); const action = items.length > 1 ? 'Request my quotes' : 'Request my quote';
  useEffect(() => {
    let active = true;
    void journey<SelectionReceipt>('/selection').then(value => {
      if (active && value.run_id === result.run_id && JSON.stringify([...selected].sort()) === JSON.stringify(value.plan_ids)) setReceipt(value);
    }).catch(() => {});
    return () => { active = false; };
  }, [result.run_id, selected]);
  async function submit() {
    if (busy || !items.length) return;
    if (!insurer) { setConsentError(true); insurerInput.current?.focus(); insurerInput.current?.scrollIntoView({ block: 'center' }); return; }
    setBusy(true); setError('');
    try {
      const consent = await journey<{ id: string }>('/consents', { purpose: 'insurer_share', recipients: [...new Set(items.map(item => item.plan.insurer_id))].sort(), accepted: true, wording_version: 'journey-sharing-v1' });
      let brokerConsent: { id: string } | undefined;
      if (broker) brokerConsent = await journey('/consents', { purpose: 'broker_share', recipients: ['helm-demo-broker'], accepted: true, wording_version: 'journey-sharing-v1' });
      const saved = await journey<SelectionReceipt>('/selection', { run_id: result.run_id, expected_version: result.profile_version, plan_ids: selected, insurer_consent_id: consent.id, broker_consent_id: brokerConsent?.id || null });
      setReceipt(saved); navigate('/get-cover/verify');
    } catch (failure) { setError(failure instanceof Error ? failure.message : 'Please retry.'); } finally { setBusy(false); }
  }
  return <>
    <h1>Review your choice</h1><div className="flow-heading-line"><p>{profileHeadline(profile)}</p><Link to={pathFor('review')}><Pencil size={15} aria-hidden="true"/> Edit my answers</Link></div>
    <p className="flow-demo-copy">This is a request for fictional quotations, with no payment or policy creation.</p>
    <div className="flow-review-grid">
      <aside className="flow-summary" aria-label="Selected plans and sharing permission"><span className="flow-plan-count">{items.length} of 3 plans chosen</span>
        {items.map(item => <PlanSummaryPanel key={item.id} item={item}/>)}
        {!items.length && <p><Link to="/get-cover/plans">Choose at least one plan before continuing.</Link></p>}
        {receipt ? <div className="flow-receipt"><p>{receipt.notice}</p><p>Reference {receipt.reference}</p><Link className="uk-button primary" to="/get-cover/verify">Continue to verification</Link></div> : <form className="flow-consent" onSubmit={event => { event.preventDefault(); void submit(); }} aria-busy={busy}>
          <label className="j-check"><input id="insurer-sharing" ref={insurerInput} type="checkbox" checked={insurer} disabled={busy} aria-invalid={consentError || undefined} aria-describedby={'selection-cta-help' + (consentError ? ' insurer-consent-error' : '')} onChange={event => { setInsurer(event.target.checked); if (event.target.checked) setConsentError(false); }}/> <span>I explicitly consent to share this reviewed fictional profile and selected plans with these named demo insurers: {[...new Set(items.map(item => item.plan.insurer_id))].join(', ') || 'none selected'}.</span></label>
          {consentError && <p id="insurer-consent-error" role="alert" className="j-error">Tick the first box to continue. Sharing with the broker is optional.</p>}
          <label className="j-check"><input type="checkbox" checked={broker} disabled={busy} onChange={event => setBroker(event.target.checked)}/> <span>Also share my case, contact and saved questions with the assigned Helm demo broker. This is optional and revocable.</span></label>
          <div className="flow-action"><div className="flow-mobile-price">{items.length === 1 ? money(items[0].quote.monthly_pence) : `${items.length} plans`}<small>{items.length === 1 ? 'per month (demo)' : 'chosen for comparison'}</small></div>
            <button className="uk-button primary" disabled={busy || !items.length} aria-disabled={!insurer || busy || !items.length} aria-describedby="selection-cta-help">{busy && <LoaderCircle className="flow-spinner" size={18} aria-hidden="true"/>}{busy ? 'Requesting…' : action}</button>
            <p id="selection-cta-help" className="flow-cta-help">{!items.length ? 'Choose a plan to continue.' : !insurer ? 'Tick the first box to continue.' : 'Next: demo WhatsApp verification.'}</p>
          </div>
        </form>}
        {error && <p role="alert" className="j-error">{error}</p>}<p className="flow-next-note">Confirm your selection, then verify your demo contact. No payment is taken.</p><BrokerContact docked/>
      </aside>
      <div className="flow-review-details"><MustHaves profile={profile}/><h2>Your details</h2><ProfileSummary profile={profile}/>
        <details className="flow-shared-fields"><summary>Exact profile fields shared with selected insurers</summary><p>Only share this reviewed fictional profile when you accept the required consent.</p><pre tabIndex={0} role="region" aria-label="Exact profile data">{JSON.stringify(profile, null, 2)}</pre></details>
      </div>
    </div>
  </>;
}
