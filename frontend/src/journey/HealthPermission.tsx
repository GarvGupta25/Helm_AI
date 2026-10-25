import { useState } from 'react';
import { Link } from 'react-router-dom';

/** Keep consent actionable beside the controls it unlocks, without changing answers. */
export default function HealthPermission({accepted,onAccept}:{accepted:boolean;onAccept:()=>Promise<void>}) {
  const [busy,setBusy]=useState(false); const [error,setError]=useState('');
  const review=<Link to="/get-cover/quote/consent">Review or withdraw processing permission</Link>;
  if(accepted)return <p>{review}</p>;
  async function enable(){
    setBusy(true);setError('');
    try{await onAccept();}catch(e){setError(e instanceof Error?e.message:'Could not save permission. Please try again.');}
    finally{setBusy(false);}
  }
  return <section className="j-notice" aria-label="Enable health preferences" aria-busy={busy}>
    <p>To choose benefit priorities, smoking answers or an existing-condition scenario, allow health-preference processing below. You can keep no preference and continue without it.</p>
    <p>I agree to process fictional health-related preferences for this comparison.</p>
    <button type="button" className="uk-button primary" disabled={busy} onClick={()=>void enable()}>
      {busy?'Saving permission…':'I agree — enable health preferences'}
    </button>
    <p>No diagnoses or medical documents. No answers are sent to an external AI provider. {review} at any time.</p>
    {busy && <p role="status">Saving permission…</p>}
    {error && <p role="alert">{error}</p>}
  </section>;
}
