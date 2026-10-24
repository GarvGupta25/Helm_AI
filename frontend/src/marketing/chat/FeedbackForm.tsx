import { useState } from 'react';
import { Flag, Send, X } from 'lucide-react';
import type { Message } from './types';

export type FeedbackTarget = { message: Message; kind: 'feedback' | 'issue'; rating?: 'up' | 'down' };
let feedbackSession = '';
function sessionId() {
  if (!feedbackSession) { try { feedbackSession = sessionStorage.getItem('helm-feedback-session') || ''; } catch { /* Memory fallback. */ } feedbackSession ||= crypto.randomUUID(); try { sessionStorage.setItem('helm-feedback-session', feedbackSession); } catch { /* Memory fallback. */ } }
  return feedbackSession;
}
export async function saveFeedback(message: Message, body: object) {
  const response = await fetch('/api/public/assistant/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId(), message_id: message.id, ...body }) });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || 'Feedback could not be saved. Please try again.');
  return data as { reference: string; recorded: boolean };
}
export function FeedbackForm({ target, onClose, onSaved }: { target: FeedbackTarget; onClose: () => void; onSaved: (notice: string) => void }) {
  const [category, setCategory] = useState(target.kind === 'issue' ? 'technical' : 'general');
  const [comment, setComment] = useState('');
  const [include, setInclude] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit() { setBusy(true); setError(''); try { const r = await saveFeedback(target.message, { kind: target.kind, rating: target.rating, category, comment, include_answer: include, answer_excerpt: include ? target.message.text.slice(0, 6000) : '' }); onSaved(`Thanks — ${target.kind === 'issue' ? 'issue report' : 'feedback'} saved. Reference ${r.reference.slice(0, 8)}.`); onClose(); } catch (e) { setError(e instanceof Error ? e.message : 'Please retry.'); } finally { setBusy(false); } }
  return <form className="hc-feedback-form" aria-label={target.kind === 'issue' ? 'Report a chat issue' : 'Response feedback'} onSubmit={e => { e.preventDefault(); void submit(); }}><div className="hc-feedback-heading"><span><Flag size={16}/>{target.kind === 'issue' ? 'Report an issue' : 'Help us improve this answer'}</span><button type="button" aria-label="Close feedback form" onClick={onClose}><X size={16}/></button></div><label>Feedback category<select aria-label="Feedback category" value={category} onChange={e => setCategory(e.target.value)}><option value="general">General feedback</option><option value="incorrect">Incorrect information</option><option value="unclear">Hard to understand</option><option value="unsafe">Safety concern</option><option value="technical">Something is not working</option><option value="other">Something else</option></select></label><label>Feedback details<textarea aria-label="Feedback details" autoFocus value={comment} onChange={e => setComment(e.target.value)} maxLength={1500} rows={3} required={target.kind === 'issue'} placeholder="Tell us what happened. No medical, identity or account details."/></label>{target.message.text && <label className="hc-feedback-check"><input type="checkbox" checked={include} onChange={e => setInclude(e.target.checked)}/> Include this assistant answer with my report</label>}<p>Only submitted feedback is saved in our separate chatbot feedback store for up to 90 days. Your conversation is not included unless you share the answer above.</p><button className="hc-feedback-submit" disabled={busy || (target.kind === 'issue' && !comment.trim())}><Send size={14}/>{busy ? 'Saving…' : 'Send feedback'}</button>{error && <p role="alert">{error}</p>}</form>;
}
