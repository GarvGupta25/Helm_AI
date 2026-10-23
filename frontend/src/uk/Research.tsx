import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import './research.css';

type Profile = { age: number; region: string; adults: number; children: number; budget_pence: number; strict_budget: boolean; excess_max_pence: number; strict_excess: boolean; required: string[]; preferred: string[]; network_min: number; existing_condition: boolean };
type Score = { score: number; components: Record<string, number>; contributions: Record<string, number> };
type Item = { id: string; plan: { name: string; network: number; limits: Record<string, number>; excess_pence: number; underwriting: string; pre_existing: string; copay: number }; quote: { monthly_pence: number; base_pence: number; tax_pence: number; annual_pence: number }; standard: Score; contextual: Score; fusion: number; alpha: number; uncertainty: string[]; evidence_ids: string[]; scenarios: Record<string, { member_pence: number; annual_total_pence: number; uncovered_pence: number; excess_pence: number; copay_pence: number }>; simulation: { mean_pence: number; median_pence: number; p90_pence: number; draws: number }; stability: Record<string, number> };
type Result = { run_id: string; items: Item[]; eligible_count: number; rejected: { id: string; reasons: { field: string; reason: string; clause_id: string | null }[] }[]; no_fit: boolean; deltas: { id: string; previous_rank: number | null; rank: number; score_delta: number | null }[]; memory_used: boolean; profile_version: number };
type Receipt = { reference: string; plan_name: string; profile_version: number; paid_pence: number; message: string; quote: Item['quote'] };
type Update = { profile: Profile; result: Result };
const initial: Profile = { age: 35, region: 'England', adults: 1, children: 0, budget_pence: 15000, strict_budget: false, excess_max_pence: 50000, strict_excess: false, required: [], preferred: [], network_min: 1, existing_condition: false };
const care = ['inpatient', 'diagnostics', 'outpatient', 'mental_health', 'physio', 'cancer', 'dental', 'maternity', 'emergency', 'chronic', 'pre_existing'];
const money = (pence: number) => new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(pence / 100);
const label = (value: string) => value.replaceAll('_', ' ');
function storedToken() { try { return sessionStorage.getItem('helm-research') || localStorage.getItem('helm-research-memory') || ''; } catch { return ''; } }

export function Research() {
  const [token, setToken] = useState(storedToken);
  const [profile, setProfile] = useState<Profile>(initial);
  const [result, setResult] = useState<Result>();
  const [hypothetical, setHypothetical] = useState<Result>();
  const [message, setMessage] = useState('');
  const [proposal, setProposal] = useState<{ proposed: Partial<Profile>; question: string }>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [memory, setMemory] = useState(false);
  const [external, setExternal] = useState(false);
  const [whyNot, setWhyNot] = useState('');
  const [explanation, setExplanation] = useState<{ reply: string; facts: { id: string; S: number; C: number; F: number; clauses: string[] }[]; why_not?: { facts?: { reasons?: { reason: string; clause_id?: string }[]; fusion?: number } }; used_in_run?: boolean; memory?: { field: string; value: string[]; observed_at: string }[] }>();
  const [selection, setSelection] = useState<Item>();
  const [receipt, setReceipt] = useState<Receipt>();
  const [acknowledgements, setAcknowledgements] = useState([false, false, false, false]);
  const [clauses, setClauses] = useState<{ id: string; text: string; status: string }[]>([]);
  async function api<T>(path: string, body?: unknown, method = 'POST', key = token): Promise<T> {
    const response = await fetch(`/api/v1${path}`, { method, headers: { 'Content-Type': 'application/json', 'X-Research-Session': key }, ...(body !== undefined ? { body: JSON.stringify(body) } : {}) });
    const data = await response.json();
    if (response.status === 410) { try { sessionStorage.removeItem('helm-research'); localStorage.removeItem('helm-research-memory'); } catch { /* Optional storage. */ } setToken(''); setResult(undefined); setMemory(false); }
    if (!response.ok) throw new Error(data.message || data.detail || 'Research service is unavailable.');
    return data as T;
  }
  async function perform(action: () => Promise<void>) { setBusy(true); setError(''); try { await action(); } catch (e) { setError(e instanceof Error ? e.message : 'Please try again.'); } finally { setBusy(false); } }
  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    void (async () => {
      try {
        const [history, consent, run, confirmation] = await Promise.all([
          api<{ profile: Profile }>('/profile/history', undefined, 'GET', token),
          api<{ durable_memory: boolean }>('/consent', undefined, 'GET', token),
          api<Result>('/recommendations', undefined, 'POST', token),
          api<{ receipt: Receipt | null }>('/quotation/confirmation', undefined, 'GET', token),
        ]);
        if (!cancelled) { setProfile(history.profile); setMemory(consent.durable_memory); setResult(run); setReceipt(confirmation.receipt || undefined); }
      } catch (e) { if (!cancelled) setError(e instanceof Error ? e.message : 'Session could not be restored.'); }
    })();
    return () => { cancelled = true; };
    // Restore only when the session capability changes.
  }, [token]);
  useEffect(() => {
    const id = receipt ? 'quote-confirmation-heading' : selection ? 'quote-review-heading' : result ? 'quote-results-heading' : '';
    if (!id) return;
    const heading = document.getElementById(id);
    heading?.focus({ preventScroll: true }); heading?.scrollIntoView({ block: 'start' });
  }, [receipt, selection, result?.run_id]);
  function accept(update: Update) { setSelection(undefined); setReceipt(undefined); setAcknowledgements([false, false, false, false]); setProfile(update.profile); setResult(update.result); setHypothetical(undefined); setProposal(undefined); }
  async function compare() {
    if (!token) {
      const data = await api<Update & { session_token: string }>('/research/sessions', profile);
      try { sessionStorage.setItem('helm-research', data.session_token); } catch { /* Optional storage. */ }
      setToken(data.session_token); accept(data);
    } else accept(await api<Update>('/profile', profile, 'PATCH'));
  }
  function change<K extends keyof Profile>(key: K, value: Profile[K]) { setProfile(p => ({ ...p, [key]: value })); }
  async function toggleMemory(enabled: boolean) {
    try { await api('/consent', { durable_memory: enabled, personalization: enabled, training: false }, 'PATCH'); } catch (e) { setMemory(!enabled); throw e; }
    setMemory(enabled);
    try { if (enabled) localStorage.setItem('helm-research-memory', token); else localStorage.removeItem('helm-research-memory'); } catch { /* Optional storage. */ }
    setNotice(enabled ? 'Confirmed soft benefit preferences saved for up to 90 days. Current needs always take precedence.' : 'Durable memory deleted. This session expires within 24 hours.');
  }
  async function confirmSelection() {
    if (!selection || !result) return;
    const confirmation = await api<Receipt>('/quotation/confirm', { run_id: result.run_id, plan_id: selection.id, profile_version: result.profile_version, understood_exclusions: acknowledgements[0], accepted_status: acknowledgements[1], received_key_facts: acknowledgements[2], simulation_only: acknowledgements[3] });
    setReceipt(confirmation); setSelection(undefined);
    document.getElementById('quote-confirmation')?.scrollIntoView({ block: 'center' });
  }
  function downloadReceipt() {
    if (!receipt) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(receipt, null, 2)], { type: 'application/json' }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'helm-demo-quote-confirmation.json'; anchor.click(); URL.revokeObjectURL(url);
  }
  const shown = hypothetical || result;
  return <div className="uk-section research">
    <div className="research-intro"><span className="uk-eyebrow">Get a quote</span><h1>Find cover that fits your needs.</h1><p>We consider all 576 synthetic policy variants, filter against your requirements and recommend up to three options. Compare costs, explanations, exclusions and what-if scenarios here before choosing.</p><p>Every insurer and price is fictional. This is a demo comparison, not regulated advice or a real insurance sale.</p><Link to="/get-cover/how-it-works">How private cover works →</Link></div>
    <div className="research-layout"><aside className="research-profile"><h2>What I understand about you</h2><p>Editable current preferences. Form edits are drafts until you confirm. Results reflect the last confirmed version. Use fictional details in this research demo.</p>
      <form onSubmit={e => { e.preventDefault(); void perform(compare); }}>
        <label>Adult age<input type="number" min="18" max="85" value={profile.age} onChange={e => change('age', +e.target.value)}/></label>
        <label>Region<select value={profile.region} onChange={e => change('region', e.target.value)}>{['England', 'London', 'Scotland', 'Wales', 'Northern Ireland'].map(r => <option key={r}>{r}</option>)}</select></label>
        <div className="research-pair"><label>Adults<select value={profile.adults} onChange={e => change('adults', +e.target.value)}><option>1</option><option>2</option></select></label><label>Children<input type="number" min="0" max="6" value={profile.children} onChange={e => change('children', +e.target.value)}/></label></div>
        <p>Synthetic family rates use the entered adult age and household counts; other members are not individually underwritten.</p><label>Monthly budget (£)<input type="number" min="0" max="10000" value={profile.budget_pence/100} onChange={e => change('budget_pence', Math.round(+e.target.value*100))}/></label>
        <label className="research-check"><input type="checkbox" checked={profile.strict_budget} onChange={e => change('strict_budget', e.target.checked)}/>Must stay within budget</label>
        <label>Maximum excess<select value={profile.excess_max_pence} onChange={e => change('excess_max_pence', +e.target.value)}>{[0, 25000, 50000].map(v => <option key={v} value={v}>{money(v)}</option>)}</select></label>
        <label className="research-check"><input type="checkbox" checked={profile.strict_excess} onChange={e => change('strict_excess', e.target.checked)}/>Excess is a hard ceiling</label>
        <label>Required hospital list<select value={profile.network_min} onChange={e => change('network_min', +e.target.value)}><option value="1">Standard fictional list</option><option value="2">Broader fictional list</option></select></label>
        <fieldset><legend>Benefit priorities</legend><p>Required needs must have explicit evidence of cover.</p>{care.map(c => <label key={c}>{label(c)}<select value={profile.required.includes(c) ? 'required' : profile.preferred.includes(c) ? 'preferred' : 'none'} onChange={e => setProfile(p => ({ ...p, required: [...p.required.filter(v => v !== c), ...(e.target.value === 'required' ? [c] : [])], preferred: [...p.preferred.filter(v => v !== c), ...(e.target.value === 'preferred' ? [c] : [])] }))}><option value="none">No preference</option><option value="preferred">Preferred</option><option value="required">Required</option></select></label>)}</fieldset>
        <label className="research-check"><input type="checkbox" checked={profile.existing_condition} onChange={e => change('existing_condition', e.target.checked)}/>Fictional scenario: required treatment is for an existing condition</label>
        <button className="uk-button" disabled={busy}>{busy ? 'Calculating…' : token ? 'Confirm & update comparison' : 'Get my recommendations'}</button>
      </form>
      {token && <><h3>Your privacy controls</h3><label className="research-check"><input type="checkbox" checked={memory} disabled={busy} onChange={e => { const enabled = e.target.checked; setMemory(enabled); void perform(() => toggleMemory(enabled)); }}/>Remember confirmed soft preferences for 90 days</label><p>Off by default. No training on visitor inputs. Your saved link is a private bearer credential on this device.</p><button onClick={() => void perform(async () => { const data = await api('/me', undefined, 'GET'); const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })); const a = document.createElement('a'); a.href = url; a.download = 'helm-research-data.json'; a.click(); URL.revokeObjectURL(url); })}>Export my data</button><button onClick={() => void perform(async () => { await api('/me', undefined, 'DELETE'); sessionStorage.removeItem('helm-research'); localStorage.removeItem('helm-research-memory'); setToken(''); setResult(undefined); setProfile(initial); setMemory(false); setReceipt(undefined); setSelection(undefined); setNotice('Session and memory deleted.'); })}>Delete session & memory</button></>}
    </aside><section className="research-results" aria-label="Synthetic comparison results">
      {receipt && <section className="research-dialogue" id="quote-confirmation" aria-label="Quote confirmation"><h2 id="quote-confirmation-heading" tabIndex={-1}>Demo confirmation</h2><p>Reference: <strong>{receipt.reference}</strong></p><p>{receipt.plan_name} · {money(receipt.quote.monthly_pence)}/month</p><p>{receipt.message}</p><p>Your selection, quote, needs summary, scores, clauses and acknowledgements are saved in this private quote session. No account is created or linked, no email is sent, and no policy is added to a dashboard. Underwriting, payment collection, insurer acceptance and policy issuance are not connected.</p><button onClick={downloadReceipt}>Download confirmation & key facts</button><button onClick={() => setReceipt(undefined)}>Return to comparison</button><Link to="/">Back to Helm</Link></section>}
      {selection && result && <section className="research-dialogue" aria-label="Review selected plan"><h2 id="quote-review-heading" tabIndex={-1}>Review your selected plan</h2><h3>{selection.plan.name}</h3><dl><div><dt>Base monthly premium</dt><dd>{money(selection.quote.base_pence)}</dd></div><div><dt>Assumed Insurance Premium Tax</dt><dd>{money(selection.quote.tax_pence)}</dd></div><div><dt>Monthly total</dt><dd>{money(selection.quote.monthly_pence)}</dd></div><div><dt>Annual total</dt><dd>{money(selection.quote.annual_pence)}</dd></div></dl><p>Excess {money(selection.plan.excess_pence)} per person/year; {selection.plan.copay*100}% co-payment. Existing conditions: {selection.plan.pre_existing}. Referral and preauthorisation apply.</p><p>Benefits used in this comparison: {result.items.find(i => i.id === selection.id)?.evidence_ids.map(id => label(id.split(':').at(-1) || '')).join(', ') || 'No benefit priorities supplied'}. Compare your confirmed needs and all limits below before continuing.</p><ul>{Object.entries(selection.plan.limits).map(([care, cap]) => <li key={care}>{label(care)}: {cap ? money(cap)+' annual limit' : 'excluded / no established cover'}</li>)}</ul><button onClick={() => void perform(async () => { const data = await api<{ clauses: typeof clauses }>(`/plans/${selection.id}`, undefined, 'GET'); setClauses(data.clauses); })}>Read selected plan key facts</button><p>These are illustrative synthetic clauses, not an approved IPID. This confirmation is not an insurance application or contract.</p>{['I understand the exclusions, limits, excess and co-payment.', 'I understand this is a fictional demo, not regulated advice.', 'I have read the selected plan key facts.', 'I understand no payment will be taken and no policy will be issued.'].map((text, index) => <label className="research-check" key={text}><input type="checkbox" checked={acknowledgements[index]} onChange={e => setAcknowledgements(values => values.map((v, i) => i === index ? e.target.checked : v))}/>{text}</label>)}<button disabled={busy || !acknowledgements.every(Boolean)} onClick={() => void perform(confirmSelection)}>Confirm demo selection (£0 collected)</button><button onClick={() => setSelection(undefined)}>Back to recommendations</button></section>}

      {error && <p role="alert" className="research-error">{error}</p>}{notice && <p role="status">{notice}</p>}
      {token && <div className="research-dialogue"><h2>Change what matters</h2><form onSubmit={e => { e.preventDefault(); void perform(async () => { if (result && /^(why|explain|compare|what.*(?:remember|past|history))/i.test(message)) { setExplanation(await api(`/recommendations/${result.run_id}/explain-chat`, { message })); setProposal(undefined); } else { setExplanation(undefined); setProposal(await api('/conversation/message', { message, external_processing_consent: external })); } }); }}><label>Describe a preference change<textarea value={message} onChange={e => setMessage(e.target.value)} maxLength={2000} placeholder="Mental health is essential; excess below £250"/></label><label className="research-check"><input type="checkbox" checked={external} onChange={e => setExternal(e.target.checked)}/>Allow this message to be sent to Groq for extraction if configured</label><button disabled={busy || !message.trim()}>Review proposed changes</button></form>{proposal && <div role="status"><p>{proposal.question}</p><dl>{Object.entries(proposal.proposed).map(([key, value]) => <div key={key}><dt>{label(key.replace("_pence", ""))}</dt><dd>{key.includes("pence") && typeof value === "number" ? money(value) : Array.isArray(value) ? value.map(label).join(", ") || "None" : typeof value === "boolean" ? value ? "Yes" : "No" : String(value)}</dd></div>)}</dl>{Object.keys(proposal.proposed).length > 0 && <button disabled={busy} onClick={() => void perform(async () => accept(await api<Update>('/profile', { ...profile, ...proposal.proposed }, 'PATCH')))}>Confirm these changes</button>}</div>}<button disabled={busy} onClick={() => void perform(async () => accept(await api<Update>('/profile/undo')))}>Undo last confirmed change</button>{explanation && <section aria-label="Grounded explanation"><p>{explanation.reply}</p>{explanation.why_not?.facts?.reasons?.map((r, i) => <p key={i}>{r.reason} <code>{r.clause_id}</code></p>)}{explanation.why_not?.facts?.fusion !== undefined && <p>Computed fusion: {explanation.why_not.facts.fusion.toFixed(1)}</p>}{explanation.facts.map(f => <p key={f.id}>{f.id}: Standard {f.S.toFixed(1)}, Context {f.C.toFixed(1)}, Fusion {f.F.toFixed(1)}. Evidence: {f.clauses.join(", ") || "No benefit priority supplied"}.</p>)}{explanation.memory && <><p>History influenced this run: {explanation.used_in_run ? "Yes" : "No"}.</p>{explanation.memory.map(m => <p key={m.field}>{label(m.field)}: {m.value.map(label).join(", ")} · confirmed {new Date(m.observed_at).toLocaleDateString("en-GB")}</p>)}</>}</section>}</div>}
      {!shown && <div className="research-empty"><h2>A comparison you can question.</h2><p>Set a budget and any essential benefits. We’ll show the calculations, gaps and synthetic evidence behind each result.</p><p>Maternity, A&E and routine chronic care are excluded in this generated catalogue. An existing condition is never assumed covered.</p></div>}
      {shown && <><div className="research-result-heading"><h2 id="quote-results-heading" tabIndex={-1}>{hypothetical ? 'What-if preview' : 'Your computed shortlist'}</h2><p>{shown.eligible_count} variants satisfy the current rules · Profile version {shown.profile_version}</p>{shown.memory_used && <p>Saved soft benefit preferences influenced this run. Current explicit needs take precedence.</p>}{hypothetical && <button onClick={() => setHypothetical(undefined)}>Return to confirmed results</button>}</div>
        {shown.no_fit && <div role="status"><h3>No generated plan meets these requirements.</h3><p>Review the failed constraints below. Change a requirement yourself to explore alternatives.</p></div>}
        <div className="research-cards">{shown.items.map((item, i) => <article key={item.id}><span className="uk-eyebrow">Synthetic option {i+1}</span><h3>{item.plan.name}</h3><strong className="research-price">{money(item.quote.monthly_pence)}<small>/month incl. assumed IPT</small></strong><p>Excess {money(item.plan.excess_pence)} per person/year · {item.plan.copay*100}% co-payment</p><p>Outpatient {money(item.plan.limits.outpatient)} · Mental health {money(item.plan.limits.mental_health)}</p><p>Hospital list {item.plan.network} · {label(item.plan.underwriting)} · Existing conditions: <strong>{item.plan.pre_existing}</strong></p>
          <div className="research-scores"><span>Standard <b>{item.standard.score.toFixed(1)}</b></span><span>Context <b>{item.contextual.score.toFixed(1)}</b></span><span>Fusion <b>{item.fusion.toFixed(1)}</b></span></div>
          <details><summary>Why this result?</summary><p>F = {item.alpha} × S + {1-item.alpha} × C. These weights are research hypotheses.</p>{(['standard', 'contextual'] as const).map(k => <div key={k}><h4>{label(k)} score contributions</h4><dl>{Object.entries(item[k].contributions).map(([name, value]) => <div key={name}><dt>{label(name)}</dt><dd>{value.toFixed(2)}</dd></div>)}</dl></div>)}<p>{item.uncertainty.join('. ')}.</p><p>Weight sensitivity: {Object.values(item.stability).map(v => v.toFixed(2)).join(' – ')} when alpha changes by ±0.05.</p></details>
          <details><summary>Exclusions & limits</summary><ul>{Object.entries(item.plan.limits).map(([name, cap]) => <li key={name}>{label(name)}: {cap ? `${money(cap)} annual cap` : 'excluded / no established cover'}</li>)}</ul><p>GP referral and preauthorisation required. Headlines never establish cover for an existing condition.</p><button onClick={() => void perform(async () => { const data = await api<{ clauses: typeof clauses }>(`/plans/${item.id}`, undefined, 'GET'); setClauses(data.clauses); })}>Read synthetic clause evidence</button></details>
          <details><summary>Simulated treatment costs</summary><p>One adult, annual caps/excess, eligible acute treatment with authorisation. Premiums are additional.</p>{Object.entries(item.scenarios).map(([name, cost]) => <p key={name}>{label(name)}: you pay {money(cost.member_pence)} including {money(cost.uncovered_pence)} uncovered. Annual premium plus this treatment scenario: {money(cost.annual_total_pence)}.</p>)}<p>{item.simulation.draws} shared fictional draws: mean {money(item.simulation.mean_pence)}, median {money(item.simulation.median_pence)}, P90 {money(item.simulation.p90_pence)}. Equal scenario weights; no prediction or maximum-loss promise.</p></details>
          {!hypothetical && <button className="uk-button" disabled={busy} onClick={() => { setSelection(item); setReceipt(undefined); setAcknowledgements([false, false, false, false]); }}>Select this plan</button>}
          <button onClick={() => void perform(async () => { await api('/feedback', { plan_id: item.id, value: 'save' }); setNotice('Saved as explicit feedback. This alone does not infer a preference or change ranking.'); })}>Save for comparison</button>
        </article>)}</div>
        {shown.items.length > 1 && <div className="research-table"><table><caption>Compare synthetic trade-offs</caption><thead><tr><th>Measure</th>{shown.items.map(i => <th key={i.id}>{i.plan.name}</th>)}</tr></thead><tbody>{['monthly', 'excess', 'outpatient', 'mental_health', 'network'].map(key => <tr key={key}><th>{label(key)}</th>{shown.items.map(i => <td key={i.id}>{key === 'network' ? i.plan.network : money(key === 'monthly' ? i.quote.monthly_pence : key === 'excess' ? i.plan.excess_pence : i.plan.limits[key])}</td>)}</tr>)}</tbody></table></div>}
        <details><summary>Why not another plan? ({shown.rejected.length} filtered)</summary><label>Search filtered variant ID<input value={whyNot} onChange={e => setWhyNot(e.target.value)} placeholder="ins-00"/></label>{shown.rejected.filter(r => r.id.includes(whyNot)).slice(0, 20).map(r => <div key={r.id}><strong>{r.id}</strong><ul>{r.reasons.map((reason, i) => <li key={i}>{reason.reason}{reason.clause_id && <code> {reason.clause_id}</code>}</li>)}</ul></div>)}<p>Showing up to 20 matching exclusions. Eligible alternatives may sit outside the family-diverse top three.</p></details>
        {result && <button disabled={busy} onClick={() => void perform(async () => { const data = await api<{ result: Result }>(`/recommendations/${result.run_id}/what-if`, { ...profile, budget_pence: profile.budget_pence+3000 }); setSelection(undefined); setReceipt(undefined); setHypothetical(data.result); })}>What if my budget rose by £30?</button>}
        {shown.deltas.length > 0 && <details><summary>Actual rank changes</summary>{shown.deltas.map(d => <p key={d.id}>{d.id}: {d.previous_rank ? `rank ${d.previous_rank} → ${d.rank}, score change ${d.score_delta}` : `new to shortlist at ${d.rank}`}</p>)}</details>}
      </>}
      {clauses.length > 0 && <section aria-label="Synthetic evidence"><h2>Synthetic clause evidence</h2><button onClick={() => setClauses([])}>Close evidence</button>{clauses.map(c => <p key={c.id} id={c.id}><code>{c.id}</code><br/>{c.text}</p>)}</section>}
    </section></div>
  </div>;
}
