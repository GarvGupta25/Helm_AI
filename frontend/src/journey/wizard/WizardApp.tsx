import { useEffect, useRef, useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, FileText, MessageCircle } from 'lucide-react';
import { journey } from '../api';
import type { Comparison } from '../Recommendations';
import BrokerContact from './BrokerContact';
import PrivacyControls from './PrivacyControls';
import { track } from './funnel';
import { firstMissing, guardedStep, pathFor, problem, skipped, stages, steps } from './steps';
import { useWizardProfile } from './useWizardProfile';
import StepFields from './StepFields';
import GuidedIntake from './GuidedIntake';
import '../journey.css';
import './wizard.css';

export default function WizardApp() {
  const model=useWizardProfile(); const {state,draft}=model; const location=useLocation(); const navigate=useNavigate();
  const id=location.pathname.replace(/^\/get-cover\/quote\/?/,''); const step=steps.find(s=>s.id===id); const index=steps.findIndex(s=>s.id===id);
  const [mode,setMode]=useState(()=>{try{return sessionStorage.getItem('helm-wizard-mode') || 'manual';}catch{return 'manual';}});
  const [busy,setBusy]=useState(false); const heading=useRef<HTMLHeadingElement>(null);
  const opened=Boolean(state);
  useEffect(()=>{heading.current?.focus();},[id,opened]);
  useEffect(()=>{document.body.classList.add('helm-wizard-active');return()=>document.body.classList.remove('helm-wizard-active');},[]);
  useEffect(()=>{document.body.dataset.wizardMode=mode;return()=>{delete document.body.dataset.wizardMode;};},[mode]);
  function choose(value:string){track('mode_chosen','choice',value==='chat'?'chat':'manual');setMode(value);try{sessionStorage.setItem('helm-wizard-mode',value);}catch{/* Memory fallback. */}window.dispatchEvent(new Event('helm-wizard-mode'));}
  async function perform(action:()=>Promise<void>){setBusy(true);model.setError('');try{await action();}catch(e){model.setError(e instanceof Error?e.message:'Please retry.');}finally{setBusy(false);}}
  async function go(next:string){if(next==='ready')await model.confirm(mode==='chat'?'guided_chat':'manual');else await model.flush();if(steps.findIndex(s=>s.id===next)>index)track('step_complete',id,mode==='chat'?'chat':'manual');navigate(pathFor(location.search.includes('return=review')?'review':next));}
  async function showPlans(){track('show_plans',id,mode==='chat'?'chat':'manual',id==='ready'?'checkpoint':id.startsWith('optional/')?'optional':'review');await model.confirm(mode==='chat'?'guided_chat':'manual');await journey<Comparison>('/recommendations?limit=10',{});navigate('/get-cover/plans');}
  if(!state || !draft)return <section className="uk-section journey wizard"><h1>Let’s find your cover.</h1><p role={model.error?'alert':'status'}>{model.error || 'Opening your private intake…'}</p>{model.error && (model.expired?<button onClick={()=>void perform(async()=>{await model.restart();navigate(pathFor());})}>Start a new private intake</button>:<button onClick={()=>window.location.reload()}>Try again</button>)}</section>;
  if(id && !step)return <Navigate to={pathFor()} replace/>;
  const guard=step && guardedStep(id,draft);if(guard)return <Navigate to={pathFor(guard)} replace/>;
  const reason=step?problem(id,draft):'';const canShow=!firstMissing(draft);const optional=step?.id.startsWith('optional/');const stageSteps=steps.filter(s=>s.stage===step?.stage);
  return <section className="uk-section journey wizard" aria-busy={busy}>
    <nav className="w-progress" aria-label="Quote stages"><ol>{stages.map((name,i)=><li key={name} aria-current={i===(step?.stage ?? 0)?'step':undefined}><span>{i+1}</span>{name}</li>)}</ol></nav>
    <div className="w-tools">{mode!=='chat' && <button type="button" onClick={()=>window.dispatchEvent(new Event('helm-open-assistant'))}>Ask Helm</button>}<Link to={pathFor('review')}>Your answers</Link><button onClick={()=>void perform(async()=>{await model.flush();choose(mode==='manual'?'chat':'manual');})}>Switch to {mode==='manual'?'guided chat':'the form'}</button><button onClick={()=>void perform(async()=>{await model.flush();})}>Save and finish later</button></div>
    <p className="uk-eyebrow" aria-live="polite">{step?`${step.tier} · Step ${stageSteps.indexOf(step)+1} of ${stageSteps.length} · ${stages[step.stage]}`:'YOUR NEEDS, BEFORE THE NUMBERS'}</p>
    <h1 ref={heading} tabIndex={-1}>{step?.title || 'A little clarity. One step at a time.'}</h1>
    <p className="w-save" role="status">{model.saving?'Saving your answers…':model.saved?'Saved in your private session.':'Unsaved changes. Saving shortly…'}</p>
    {model.error && <div className="j-error" role="alert">{model.error}<button onClick={()=>void perform(async()=>{await model.flush();})}>Retry saving</button></div>}
    {!step?<><p className="uk-lead">About five minutes. Choose how you’d like to tell us what matters. Switch at any time.</p><div className="w-mode-cards">{[['manual','Fill it in myself','Simple questions, at your own pace.'],['chat','Let the AI ask me','Guided questions with clear answers and a review.']].map(([value,title,text])=><button key={value} onClick={()=>{choose(value);navigate(pathFor('consent'));}}>{value==='manual'?<FileText/>:<MessageCircle/>}<strong>{title}</strong><span>{text}</span><ArrowRight size={20}/></button>)}</div></>:<div className="w-step">{mode==='chat' && !['consent','ready','review'].includes(id)?<GuidedIntake key={id} id={id} model={model}/>:<StepFields key={id} id={id} model={model}/>}</div>}
    {step && <div className="w-action"><button onClick={()=>void perform(()=>go(steps[index-1]?.id || ''))}><ArrowLeft size={16}/> Back</button>{optional && <button disabled={busy || !canShow} onClick={()=>void perform(showPlans)}>Show my plans</button>}<span id="w-next-reason">{reason || (optional?'Optional answers can be added later.':'Your draft is saved before continuing.')}</span>{step.tier==='Optional' && mode!=='chat' && <button onClick={()=>void perform(async()=>{for(const [key,value] of Object.entries(skipped(id,draft)))model.change(key as keyof typeof draft,value as never);await go(steps[index+1]?.id || 'review');})}>Skip</button>}<button className="uk-button primary" disabled={busy || !!reason} aria-describedby="w-next-reason" onClick={()=>void perform(()=>['ready','review'].includes(id)?showPlans():go(steps[index+1]?.id || 'review'))}>{['ready','review'].includes(id)?'Show my plans':'Next'} <ArrowRight size={16}/></button><BrokerContact docked prepare={()=>model.confirm(mode==='chat'?'guided_chat':'manual')}/></div>}
    <PrivacyControls prepare={()=>model.flush()}/>
    {!step && <BrokerContact docked prepare={()=>model.confirm(mode==='chat'?'guided_chat':'manual')}/>}
  </section>;
}
