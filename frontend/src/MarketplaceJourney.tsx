import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowRight, Check, Clock3 } from 'lucide-react';
import { api, aed, post } from './api';
import { ErrorView, Loading } from './Feedback';

const steps = [
  ['sent_to_providers', 'Requested'], ['quotation_received', 'Quotation received'],
  ['quotes_collected', 'Final comparison'], ['customer_selected', 'Choice sent'],
  ['provider_accepted', 'Provider accepted'], ['broker_final_review', 'Final review complete'],
  ['bound', 'Policy started'],
];
const nextSteps: Record<string, string> = {
  customer_selected: 'Your choice is with the provider. They will accept the submitted terms next.',
  provider_accepted: 'Your provider accepted your choice. The assigned broker will review the final terms.',
  broker_final_review: 'Final review is complete. Your provider can now start the demonstration policy.',
  bound: 'Your demonstration policy has started. Open Policies & cover to view it or raise a claim.',
};
type Quotation = {
  quotation_id: string; provider_name: string; premium_aed: number; status: string;
  rank?: number; name?: string; explanation?: string; terms: Record<string, unknown>;
};
type Journey = {
  status: string; invited: number; responded: number; collection_ready: boolean;
  collection_window_hours: number; quotations: Quotation[]; updates?: Quotation[];
};
type Recommendation = { plan_id: string; rank: number; name: string; provider_name: string; premium_aed: number };

function term(value: unknown): string {
  if (value == null) return 'Not provided';
  if (typeof value === 'boolean') return value ? 'Included' : 'Not included';
  if (typeof value === 'object') {
    const benefit = value as { covered?: boolean; waiting_period_months?: number; limit?: number };
    if (benefit.covered === false) return 'Not included';
    if (benefit.covered === true) return `${benefit.waiting_period_months ? `After ${benefit.waiting_period_months} months` : 'From day one'}${benefit.limit ? ` · ${aed(Number(benefit.limit) * 100)} limit` : ''}`;
    return 'See provider terms';
  }
  return String(value);
}

function QuotationTerms({ terms }: { terms: Record<string, unknown> }) {
  return <dl className="term-list">{Object.entries(terms).filter(([key]) => !['id', 'name', 'annual_premium'].includes(key)).map(([key, value]) => <div key={key}>
    <dt>{key.replaceAll('_', ' ')}</dt><dd>{['annual_limit', 'deductible'].includes(key) && value != null ? aed(Number(value) * 100) : key === 'outpatient_copay_pct' && value != null ? `${value}%` : term(value)}</dd>
  </div>)}</dl>;
}

export function MarketplaceJourney() {
  const { caseId = '' } = useParams();
  const query = useQueryClient();
  const [busy, setBusy] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [plans, setPlans] = useState<string[]>([]);
  const [choice, setChoice] = useState<Quotation | null>(null);
  const confirmation = useRef<HTMLHeadingElement>(null);
  const status = useQuery<Journey>({ queryKey: ['marketplace-status', caseId], queryFn: () => api(`/api/marketplace/cases/${caseId}/quotations`), refetchInterval: result => ['bound', 'declined'].includes(result.state.data?.status || '') ? false : 5000 });
  const recommendations = useQuery<{ recommendations: Recommendation[]; explanations: { plan_id: string; explanation: string }[] }>({ queryKey: ['marketplace-recommendations', caseId], queryFn: () => api(`/api/marketplace/cases/${caseId}/recommendations`), enabled: status.data?.invited === 0, retry: false });
  useEffect(() => { if (choice) confirmation.current?.focus(); }, [choice]);

  async function requestQuotes() {
    if (busy) return;
    setBusy('request'); setMessage(''); setError('');
    try {
      await post(`/api/marketplace/cases/${caseId}/consent`, { consent: 'yes', plan_ids: plans });
      await status.refetch();
      await query.invalidateQueries({ queryKey: ['marketplace-applications'] });
      setMessage('Your confirmed profile was sent only to the providers you selected.');
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'The provider request could not be saved.'); }
    finally { setBusy(''); }
  }
  async function confirmChoice() {
    if (!choice || busy) return;
    setBusy(choice.quotation_id); setMessage(''); setError('');
    try {
      await post(`/api/marketplace/quotations/${choice.quotation_id}/select`);
      setChoice(null);
      await status.refetch();
      await query.invalidateQueries({ queryKey: ['marketplace-notifications'] });
      setMessage('Your choice was sent to the provider. Provider acceptance and final broker review come before policy activation.');
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'The quotation could not be selected.'); }
    finally { setBusy(''); }
  }
  function toggle(id: string) {
    setPlans(current => current.includes(id) ? current.filter(item => item !== id) : current.length < 3 ? [...current, id] : current);
  }
  if (status.isLoading) return <Loading/>;
  if (status.error) return <><ErrorView error={status.error}/><button className="secondary" onClick={() => void status.refetch()}>Retry provider updates</button></>;
  const data = status.data!;
  const active = Math.max(0, steps.findIndex(([state]) => state === data.status));
  const canChoose = data.status === 'quotes_collected';
  return <>
    <div className="page-heading compact"><div><span className="eyebrow">YOUR MARKETPLACE</span><h1>{data.invited ? 'Your provider quotations' : 'Your five best matches'}</h1><p>{data.invited ? 'Follow responses here. You control every choice.' : 'Helm matched these plans using the details you confirmed.'}</p></div><span className="badge neutral">{data.status.replaceAll('_', ' ')}</span></div>
    {data.invited > 0 && <ol className="marketplace-timeline" aria-label="Quotation and policy progress">{steps.map(([state, label], index) => <li aria-current={index === active ? 'step' : undefined} className={index < active ? 'complete' : index === active ? 'active' : ''} key={state}><span>{index < active ? <Check size={14}/> : index + 1}</span><small>{label}</small></li>)}</ol>}
    <div role="status" aria-live="polite">{nextSteps[data.status] && <div className="notice">{nextSteps[data.status]}</div>}{message && <div className="notice">{message}</div>}</div>
    {error && <ErrorView error={new Error(error)}/>}
    {data.status === 'bound' && <Link className="button" to="/app">Open policies & cover <ArrowRight size={17}/></Link>}
    {data.invited === 0 ? <section className="surface">
      <span className="eyebrow">HELM'S RECOMMENDATIONS</span><h2>Choose up to three options for final quotations</h2>
      <p className="muted">Select plans below. By requesting quotations, you authorize Helm to share your confirmed insurance profile with only the selected providers.</p>
      {recommendations.isLoading ? <Loading/> : recommendations.error ? <><ErrorView error={recommendations.error}/><Link className="text-link" to={`/app/intake/${caseId}`}>Review your profile</Link></> : !recommendations.data?.recommendations.length ? <div className="empty-state"><h3>No plans match these requirements</h3><p>Review your budget and cover needs, then request new recommendations.</p><Link className="button secondary" to={`/app/intake/${caseId}`}>Edit profile</Link></div> : <>
        <div className="plan-grid">{recommendations.data.recommendations.map(item => <button type="button" disabled={!!busy} className={`plan-card ${plans.includes(item.plan_id) ? 'recommended' : ''}`} key={item.plan_id} onClick={() => toggle(item.plan_id)} aria-pressed={plans.includes(item.plan_id)}>
          <div className="plan-top"><span className="eyebrow">#{item.rank} · {item.provider_name}</span><span className="badge neutral">{plans.includes(item.plan_id) ? 'Selected' : 'Select'}</span></div>
          <h3>{item.name}</h3><strong className="plan-price">{aed(item.premium_aed * 100)}<small>/ year estimate</small></strong><p>{recommendations.data.explanations.find(reason => reason.plan_id === item.plan_id)?.explanation}</p>
        </button>)}</div>
        <p role="status">{plans.length} of 3 options selected.</p><button disabled={!!busy || !plans.length} onClick={() => void requestQuotes()}>{busy === 'request' ? 'Sending…' : 'Request selected quotations'} <ArrowRight size={17}/></button>
      </>}
    </section> : !data.collection_ready ? <>
      <section className="empty-state"><Clock3 size={32}/><h2>Providers are preparing quotations</h2><p>{data.responded} of {data.invited} selected {data.invited === 1 ? 'provider has' : 'providers have'} responded. Final comparison opens when all reply, or after the {data.collection_window_hours}-hour collection window if at least one quotation is available.</p><button className="secondary" disabled={status.isFetching} onClick={() => void status.refetch()}>Check for updates</button></section>
      {!!data.updates?.length && <section className="surface"><span className="eyebrow">NEW PROVIDER QUOTATIONS</span><h2>Review responses received so far</h2><div className="plan-grid">{data.updates.map(item => <article className="plan-card" key={item.quotation_id}><div className="plan-top"><span className="eyebrow">{item.provider_name}</span><span className="badge success">Quotation received</span></div><strong className="plan-price">{aed(item.premium_aed * 100)}<small>/ year</small></strong><QuotationTerms terms={item.terms}/><p className="muted">Final ranking is waiting for the remaining providers or the collection window.</p></article>)}</div></section>}
    </> : <>
      <section className="surface"><span className="eyebrow">FINAL QUOTATIONS</span><h2>{canChoose ? "Helm's best fit is ranked first" : 'Your selected quotation'}</h2><p className="muted">{data.responded} of {data.invited} providers responded. Compare the submitted terms. Plans, prices and policies are fictional demonstration data.</p></section>
      {!data.quotations.length && <div className="empty-state"><h3>No eligible quotation to compare</h3><p>Submitted terms do not match the current profile. Review your requirements or contact your broker.</p><Link className="text-link" to={`/app/intake/${caseId}`}>Review profile</Link></div>}
      <div className="plan-grid">{data.quotations.map(item => <article className={`plan-card ${item.rank === 1 ? 'recommended' : ''}`} key={item.quotation_id}><div className="plan-top"><span className="eyebrow">#{item.rank} · {item.provider_name}</span>{item.rank === 1 && <span className="badge">Helm's best fit</span>}</div><h3>{item.name}</h3><strong className="plan-price">{aed(item.premium_aed * 100)}<small>/ year</small></strong><p>{item.explanation}</p><QuotationTerms terms={item.terms}/>{canChoose && ['submitted', 'shortlisted'].includes(item.status) ? <button disabled={!!busy} onClick={() => setChoice(item)}>Choose this quotation <ArrowRight size={17}/></button> : <p className="broker-approved"><Check size={17}/>{nextSteps[data.status] || item.status}</p>}</article>)}</div>
    </>}
    {choice && <section className="surface"><span className="eyebrow">CONFIRM YOUR CHOICE</span><h2 ref={confirmation} tabIndex={-1}>Choose {choice.provider_name}?</h2><p>You selected {choice.name} at {aed(choice.premium_aed * 100)} per year. Confirming sends your choice to the provider. Provider acceptance and final broker review are required before activation.</p><div className="actions"><button disabled={!!busy} onClick={() => void confirmChoice()}>{busy ? 'Confirming…' : 'Yes, confirm this policy'} <Check size={17}/></button><button className="secondary" disabled={!!busy} onClick={() => setChoice(null)}>No, compare again</button></div></section>}
    <Link className="text-link" to="/app">Back to workspace</Link>
  </>;
}
