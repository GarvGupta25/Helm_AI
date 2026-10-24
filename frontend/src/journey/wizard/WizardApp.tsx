import { useEffect, useRef, useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, FileText, MessageCircle } from 'lucide-react';
import { journey } from '../api';
import type { Comparison } from '../Recommendations';
import BrokerHandoff from '../BrokerHandoff';
import { guardedStep, pathFor, problem, stages, steps } from './steps';
import { useWizardProfile } from './useWizardProfile';
import '../journey.css';
import './wizard.css';

export default function WizardApp() {
  const model=useWizardProfile(); const {state,draft}=model; const location=useLocation(); const navigate=useNavigate();
  const id=location.pathname.replace(/^\/get-cover\/quote\/?/,''); const step=steps.find(s=>s.id===id); const index=steps.findIndex(s=>s.id===id);
  const [mode,setMode]=useState(()=>{try{return sessionStorage.getItem('helm-wizard-mode') || 'manual';}catch{return 'manual';}});
  const [busy,setBusy]=useState(false); const heading=useRef<HTMLHeadingElement>(null);
  useEffect(()=>{heading.current?.focus();},[id]);
  function choose(value:string){setMode(value);try{sessionStorage.setItem('helm-wizard-mode',value);}catch{/* Memory fallback. */}window.dispatchEvent(new Event('helm-wizard-mode'));}
  async function perform(action:()=>Promise<void>){setBusy(true);model.setError('');try{await action();}catch(e){model.setError(e instanceof Error?e.message:'Please retry.');}finally{setBusy(false);}}
  async function go(next:string){await model.flush();navigate(pathFor(next));}
  async function showPlans(){await model.confirm(mode==='chat'?'guided_chat':'manual');await journey<Comparison>('/recommendations',{});navigate('/get-cover/plans');}
  if(!state || !draft)return <section className="uk-section journey wizard"><h1>Let’s find your cover.</h1><p role={model.error?'alert':'status'}>{model.error || 'Opening your private intake…'}</p>{model.error && <button onClick={()=>window.location.reload()}>Try again</button>}</section>;
  if(id && !step)return <Navigate to={pathFor()} replace/>;
  const guard=step && guardedStep(id,draft);if(guard)return <Navigate to={pathFor(guard)} replace/>;
  const reason=step?problem(id,draft):'';const stageSteps=steps.filter(s=>s.stage===step?.stage);
  return <section className="uk-section journey wizard" aria-busy={busy}>
    <nav className="w-progress" aria-label="Quote stages"><ol>{stages.map((name,i)=><li key={name} aria-current={i===(step?.stage ?? 0)?'step':undefined}><span>{i+1}</span>{name}</li>)}</ol></nav>
    <div className="w-tools"><Link to={pathFor('review')}>Your answers</Link><button onClick={()=>void perform(async()=>{await model.flush();choose(mode==='manual'?'chat':'manual');})}>Switch to {mode==='manual'?'guided chat':'the form'}</button><button onClick={()=>void perform(async()=>{await model.flush();})}>Save and finish later</button></div>
    <p className="uk-eyebrow" aria-live="polite">{step?`${step.tier} · Step ${stageSteps.indexOf(step)+1} of ${stageSteps.length} · ${stages[step.stage]}`:'YOUR NEEDS, BEFORE THE NUMBERS'}</p>
    <h1 ref={heading} tabIndex={-1}>{step?.title || 'A little clarity. One step at a time.'}</h1>
    <p className="w-save" role="status">{model.saving?'Saving your answers…':model.saved?'Saved in your private session.':'Unsaved changes. Saving shortly…'}</p>
    {model.error && <div className="j-error" role="alert">{model.error}<button onClick={()=>void perform(async()=>{await model.flush();})}>Retry saving</button></div>}
    {!step?<><p className="uk-lead">About five minutes. Choose how you’d like to tell us what matters. Switch at any time.</p><div className="w-mode-cards">{[['manual','Fill it in myself','Simple questions, at your own pace.'],['chat','Let the AI ask me','Guided questions with clear answers and a review.']].map(([value,title,text])=><button key={value} onClick={()=>{choose(value);navigate(pathFor('consent'));}}>{value==='manual'?<FileText/>:<MessageCircle/>}<strong>{title}</strong><span>{text}</span><ArrowRight size={20}/></button>)}</div></>:<div className="w-step"><p>{mode==='chat'?'Guided questions are coming in Phase 4. You can use the form now without losing your answers.':'Your answers stay in the same private profile. Question controls are added in the next phase.'}</p>{mode==='chat' && <button onClick={()=>choose('manual')}>Use the form</button>}</div>}
    {step && <div className="w-action"><button onClick={()=>void perform(()=>go(steps[index-1]?.id || ''))}><ArrowLeft size={16}/> Back</button><span id="w-next-reason">{reason || 'Your draft is saved before continuing.'}</span>{step.tier==='Optional' && <button onClick={()=>void perform(()=>go(steps[index+1]?.id || 'review'))}>Skip</button>}<button className="uk-button primary" disabled={busy || !!reason} aria-describedby="w-next-reason" onClick={()=>void perform(()=>id==='review'?showPlans():go(steps[index+1]?.id || 'review'))}>Next <ArrowRight size={16}/></button></div>}
    <BrokerHandoff prepare={()=>model.confirm(mode==='chat'?'guided_chat':'manual')}/>
  </section>;
}
