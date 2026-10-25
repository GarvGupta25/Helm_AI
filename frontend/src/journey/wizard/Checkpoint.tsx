import type { RefObject } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Check, LockKeyhole, LoaderCircle } from 'lucide-react';
import { ProfileSummary } from './ProfileSummary';
import { SaveExitForm } from './Checkout';
import { pathFor } from './steps';
import PrivacyControls from './PrivacyControls';
import BrokerContact from './BrokerContact';
import type { useWizardProfile } from './useWizardProfile';

export default function Checkpoint({ model, mode, busy, heading, onPlans, onBack, onSwitch }: { model: ReturnType<typeof useWizardProfile>; mode: string; busy: boolean; heading: RefObject<HTMLHeadingElement | null>; onPlans: () => void; onBack: () => void; onSwitch: () => void }) {
  return <section className="uk-section journey wizard checkout-flow flow-checkpoint" aria-busy={busy}>
    <div className="flow-checkpoint-progress"><span>Step 7 of 7</span><span><Check size={16} aria-hidden="true"/> Essentials complete</span><progress max={7} value={7} aria-label="Essentials complete: step 7 of 7"/></div>
    <h1 ref={heading} tabIndex={-1}><Check size={28} aria-hidden="true"/> Your essentials are done</h1>
    <p className="flow-saved" role="status"><LockKeyhole size={15} aria-hidden="true"/>{model.saving ? 'Saving your answers…' : model.saved ? 'Saved in your private session' : 'Unsaved changes. Saving shortly…'}</p>
    {model.error && <p className="j-error" role="alert">{model.error}</p>}
    <p>Check your essentials, then explore the plans that fit. All plans and quotations in this journey are fictional.</p>
    <div className="flow-checkpoint-actions"><button className="uk-button primary" disabled={busy} onClick={onPlans}>{busy && <LoaderCircle className="flow-spinner" size={18} aria-hidden="true"/>}{busy ? 'Finding your plans…' : 'See my plans'}</button><div><Link className="uk-button secondary" to={pathFor('optional/existing-cover')}>Add optional details (about 2 min)</Link><p>Narrows results to plans that fit you better.</p></div></div>
    <ProfileSummary profile={model.draft!}/>
    <div className="flow-secondary-tools"><button disabled={busy} onClick={onBack}><ArrowLeft size={16} aria-hidden="true"/> Back to essential answers</button><Link to={pathFor('review')}>Review all answers</Link></div>
    <details className="flow-more-options"><summary>More ways to continue</summary><button disabled={busy} onClick={onSwitch}>Switch to {mode==='manual'?'guided chat':'the form'}</button><BrokerContact docked prepare={() => model.confirm(mode==='chat'?'guided_chat':'manual')}/></details>
    <PrivacyControls prepare={() => model.flush()}/><SaveExitForm prepare={() => model.flush()} onError={model.setError}/>
  </section>;
}
