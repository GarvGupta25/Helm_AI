import { useEffect, useState, type ReactNode, type ButtonHTMLAttributes, type InputHTMLAttributes } from 'react';
import { Link } from 'react-router-dom';
import * as Tooltip from '@radix-ui/react-tooltip';
import * as Tabs from '@radix-ui/react-tabs';
import { ArrowUpRight } from 'lucide-react';

export function useReducedMotion() {
  const [reduced, setReduced] = useState(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => { const media = matchMedia('(prefers-reduced-motion: reduce)'); const update = () => setReduced(media.matches); media.addEventListener('change', update); return () => media.removeEventListener('change', update); }, []);
  return reduced;
}
export function Button({ children, variant = 'primary', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' }) { return <button {...props} className={`uk-button ${variant} ${props.className || ''}`}>{children}</button>; }
export function Action({ to, children, secondary = false }: { to: string; children: ReactNode; secondary?: boolean }) { return <Link to={to} className={`uk-button ${secondary ? 'secondary' : 'primary'}`}>{children}<ArrowUpRight size={18} aria-hidden="true"/></Link>; }
export function Eyebrow({ children }: { children: ReactNode }) { return <p className="uk-eyebrow">{children}</p>; }
export function Badge({ children }: { children: ReactNode }) { return <span className="uk-badge">{children}</span>; }
export function Card({ children }: { children: ReactNode }) { return <article className="uk-card">{children}</article>; }
export function Field({ label, error, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string }) { const id = props.id || props.name || label.replace(/\W/g, '-'); return <label className="uk-field" htmlFor={id}>{label}<input {...props} id={id} aria-invalid={!!error} aria-describedby={error ? `${id}-error` : undefined}/>{error && <span role="alert" id={`${id}-error`}>{error}</span>}</label>; }
export function Check({ children, ...props }: InputHTMLAttributes<HTMLInputElement> & { children: ReactNode }) { return <label className="uk-check"><input {...props} type="checkbox"/>{children}</label>; }
export function Accordion({ title, children }: { title: string; children: ReactNode }) { return <details className="uk-accordion"><summary>{title}<span aria-hidden="true">＋</span></summary><div>{children}</div></details>; }
export { SheetModal as Modal } from './SheetModal';
export function GlossaryTip({ term, children }: { term: string; children: ReactNode }) { return <Tooltip.Provider delayDuration={200}><Tooltip.Root><Tooltip.Trigger className="uk-term">{term}</Tooltip.Trigger><Tooltip.Portal><Tooltip.Content className="uk-tooltip" sideOffset={8}>{children}<Tooltip.Arrow/></Tooltip.Content></Tooltip.Portal></Tooltip.Root></Tooltip.Provider>; }
export function NarrativeTabs() { return <Tabs.Root defaultValue="why" className="uk-narrative"><Tabs.List aria-label="Our approach">{[['why', 'Why we exist'], ['how', 'How we work'], ['next', 'Where we’re going']].map(([id, text]) => <Tabs.Trigger value={id} key={id}>{text}</Tabs.Trigger>)}</Tabs.List>{[
  ['why', 'Cover shouldn’t come with a decoder ring.', 'Clear answers help you make a considered choice. We put the exclusions next to the benefits, and the tax next to the price.'],
  ['how', 'See the detail. Keep the choice.', 'Tell us what matters. Compare fictional plans by price, hospital list and benefits. A human adviser can help when you need one.'],
  ['next', 'A little more human. Every step.', 'Our aim is clearer documents, more accessible journeys and support that meets you where you are. This demonstration helps us test those ideas.'],
].map(([id, title, text]) => <Tabs.Content value={id} key={id}><Eyebrow>THE HELM APPROACH</Eyebrow><h2>{title}</h2><p>{text}</p><Link to="/consumer-duty">How we put understanding first ↗</Link></Tabs.Content>)}</Tabs.Root>; }
export function Skeleton() { return <div className="uk-skeleton" role="status" aria-label="Loading content"/>; }
export function Toast({ children }: { children: ReactNode }) { return <p className="uk-toast" role="status">{children}</p>; }
