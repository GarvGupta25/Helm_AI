import { useState, type ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Check, ChevronRight, LockKeyhole, Pencil } from 'lucide-react';
import type { Profile } from '../api';
import { pathFor } from './steps';
import { mustHaves } from './checkoutPresentation';
import './checkout.css';

export function FlowStepper() {
  return <nav className="flow-stepper" aria-label="Quote progress"><ol>
    <li><Link to="/get-cover/plans"><Check size={16} aria-hidden="true"/><span>Plans<span className="uk-sr"> completed</span></span></Link><ChevronRight size={14} aria-hidden="true"/></li>
    <li><Link to="/get-cover/compare">Compare<span className="uk-sr"> (optional)</span></Link><ChevronRight size={14} aria-hidden="true"/></li>
    <li aria-current="step"><span className="flow-step-number">3</span> Review</li>
  </ol></nav>;
}

export function DetailRow({ label, children, edit, editLabel }: { label: string; children: ReactNode; edit: string; editLabel: string }) {
  return <div className="flow-detail-row"><dt>{label}</dt><dd><span>{children}</span><Link to={pathFor(edit) + '?return=review'} aria-label={editLabel}><Pencil size={15} aria-hidden="true"/><span>Edit</span></Link></dd></div>;
}

export function MustHaves({ profile }: { profile: Profile }) {
  const requirements = mustHaves(profile);
  return <section className="flow-must-haves" aria-label="Your must-haves"><LockKeyhole size={18} aria-hidden="true"/><div>
    <p><strong>Your must-haves are set.</strong> {requirements.length ? requirements.join(', ') + '.' : 'No extra limits or essential benefits selected.'} Every plan you see meets these.</p>
    <details><summary>What does this mean?</summary><p>These are your confirmed answers. Display filters only narrow eligible options; they cannot relax these requirements.</p><Link to={pathFor('review')}>Edit in my answers</Link></details>
  </div></section>;
}

export function SaveExitForm({ prepare, onError }: { prepare: () => Promise<unknown>; onError: (message: string) => void }) {
  const navigate = useNavigate(); const [busy, setBusy] = useState(false);
  return <form id="checkout-save" aria-busy={busy} onSubmit={event => {
    event.preventDefault(); if (busy) return; setBusy(true);
    void prepare().then(() => navigate('/')).catch(error => onError(error instanceof Error ? error.message : 'Your answers could not be saved. Please try again.')).finally(() => setBusy(false));
  }}>{busy && <p role="status">Saving your answers before you leave…</p>}</form>;
}
