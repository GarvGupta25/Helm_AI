import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api, aed, post } from '../api';
import { ErrorView, Loading } from '../Feedback';
import type { ProviderPolicy, ProviderQuotation } from './types';

export function ProviderPolicies({ selectedPolicy, onSelectPolicy }: { selectedPolicy: string; onSelectPolicy: (id: string) => void }) {
  const query = useQueryClient();
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const quotations = useQuery<ProviderQuotation[]>({ queryKey: ['provider-quotations'], queryFn: () => api('/api/provider/quotations'), refetchInterval: 5000 });
  const policies = useQuery<ProviderPolicy[]>({ queryKey: ['provider-policies'], queryFn: () => api('/api/provider/policies'), refetchInterval: 5000 });

  async function action(path: string, success: string, body: unknown = {}) {
    if (busy) return;
    setBusy(true); setMessage(''); setError('');
    try {
      await post(path, body);
      await Promise.all([
        query.invalidateQueries({ queryKey: ['provider-quotations'] }),
        query.invalidateQueries({ queryKey: ['provider-policies'] }),
      ]);
      setMessage(success);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'The provider record could not be updated.'); }
    finally { setBusy(false); }
  }

  return <section className="surface" aria-busy={busy}>
    <span className="eyebrow">QUOTES & POLICIES</span><h2>Portfolio</h2>
    {message && <p className="notice" role="status">{message}</p>}
    {error && <ErrorView error={new Error(error)}/>}
    <h3>Quotations</h3>
    {quotations.isLoading && <Loading/>}
    {quotations.error && <ErrorView error={quotations.error}/>}
    {quotations.data?.map(quote => <div className="list-row" key={quote.id}>
      <div><strong>{aed(quote.premium * 100)} · {quote.status}</strong><small>Application {quote.application_id.slice(0, 8)}</small></div>
      {quote.status === 'selected' && <button disabled={busy} onClick={() => void action(`/api/provider/quotations/${quote.id}/accept`, 'Quotation accepted. The assigned broker will review the final terms before activation.')}>Accept quotation</button>}
      {quote.status === 'accepted' && (quote.application_status === 'bound'
        ? <span className="badge success">Policy started</span>
        : quote.application_status === 'broker_final_review'
          ? <button disabled={busy} onClick={() => void action(`/api/provider/policies/${quote.id}/start`, 'Demonstration policy started and saved to the member and provider workspaces.')}>Start policy</button>
          : <span className="badge neutral">Awaiting broker final review</span>)}
    </div>)}
    {!quotations.isLoading && !quotations.error && !quotations.data?.length && <p>No quotations yet.</p>}
    <h3>Policies</h3>
    {policies.isLoading && <Loading/>}
    {policies.error && <ErrorView error={policies.error}/>}
    {policies.data?.map(policy => <div className={`list-row provider-policy ${selectedPolicy === policy.id ? 'selected' : ''}`} key={policy.id}>
      <button className="quiet" aria-pressed={selectedPolicy === policy.id} onClick={() => onSelectPolicy(policy.id)}><strong>Policy {policy.id.slice(0, 8)}</strong><small>{policy.status}</small></button>
      {policy.status === 'active' && <button className="secondary" disabled={busy} onClick={() => {
        const reason = window.prompt('Reason for discontinuation');
        if (reason) void action(`/api/provider/policies/${policy.id}/discontinue`, 'Policy discontinued.', { reason });
      }}>Discontinue</button>}
    </div>)}
    {!policies.isLoading && !policies.error && !policies.data?.length && <p>No active policies yet. Accept a member selection, wait for final broker review, then start its policy.</p>}
  </section>;
}
