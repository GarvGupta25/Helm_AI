import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowRight, Building2, HeartPulse, ShieldCheck } from 'lucide-react';
import { PageShell, Section } from '../components';
import { api, aed } from '../../api';
import './PlansPage.css';

function coverageLabel(plan: any) {
  if (plan.maternity?.covered) return plan.maternity.waiting_period_months ? `Maternity after ${plan.maternity.waiting_period_months} months` : 'Maternity from day one';
  return 'General health cover';
}

export function PlansPage() {
  const [search, setSearch] = useState('');
  const [network, setNetwork] = useState('all');
  const [params, setParams] = useSearchParams();
  const provider = params.get('provider');
  const { data: catalogue, error, isLoading, refetch } = useQuery({ queryKey: ['marketplace-plans'], queryFn: () => api('/api/public/marketplace-plans') });
  const plans = (catalogue?.plans || []).filter((plan: any) => (!provider || plan.provider_id === provider) && (network === 'all' || plan.network === network) && `${plan.name} ${plan.provider_name}`.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase()));
  function clear() { setSearch(''); setNetwork('all'); setParams({}); }
  return <PageShell>
    <Section id="plans-hero" tinted><div className="plans-hero"><span className="plans-kicker"><ShieldCheck size={16}/> Fictional UAE marketplace</span><h1>Find the cover that fits your next step.</h1><p>Explore fictional Helm schemes. Every card gives you the essentials; open it for the full benefit details.</p><div className="plans-hero-stats"><span><strong>10</strong> demo partners</span><span><strong>50</strong> schemes</span><span><strong>5</strong> cover styles</span></div></div></Section>
    <Section id="plans-catalogue">
      <div className="catalogue-filters"><label className="field">Search schemes<input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Scheme or partner name"/></label><label className="field">Network<select value={network} onChange={event => setNetwork(event.target.value)}><option value="all">All networks</option><option value="restricted">Restricted</option><option value="standard">Standard</option><option value="wide">Wide</option></select></label><button type="button" className="secondary" onClick={clear}>Clear filters</button></div>
      {isLoading && <p className="plans-loading" role="status">Loading schemes…</p>}
      {error && <div className="plans-error" role="alert"><p>The scheme catalogue is unavailable.</p><button className="secondary" onClick={() => void refetch()}>Retry catalogue</button></div>}
      {!isLoading && !error && <><p role="status">{plans.length} {plans.length === 1 ? 'scheme' : 'schemes'} found{provider ? ' for this partner' : ''}.</p>{!plans.length ? <div className="empty-state"><h2>No schemes found</h2><p>Try another name or clear your filters to see available demonstration schemes.</p><button className="secondary" onClick={clear}>Show all schemes</button></div> : <div className="scheme-grid" aria-label="Popular schemes">{plans.map((plan: any, index: number) => <Link to={`/plans/${plan.id}`} className="scheme-card" key={plan.id}><div className="scheme-card__top"><span className={`scheme-network scheme-network--${plan.network}`}>{plan.network} network</span><span className="scheme-card__number">{String(index + 1).padStart(2, '0')}</span></div><div><p className="scheme-provider"><Building2 size={14}/>{plan.provider_name}</p><h2>{(plan.name || 'Unnamed scheme').replace(`${plan.provider_name} `, '')}</h2></div><div className="scheme-price"><strong>{aed(plan.annual_premium * 100)}</strong><span>per year</span></div><div className="scheme-highlights"><span><HeartPulse size={15}/>{coverageLabel(plan)}</span><span>{aed(plan.annual_limit * 100)} annual limit</span></div><div className="scheme-card__action">View full details <ArrowRight size={17}/></div></Link>)}</div>}</>}
    </Section>
  </PageShell>;
}
