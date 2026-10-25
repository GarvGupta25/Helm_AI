import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { journey, type IntakeState, type Profile } from '../api';
import { pathFor } from './steps';
import { track } from './funnel';
import { ProfileSummary } from './StepFields';
import type { useWizardProfile } from './useWizardProfile';

type Turn = {state:IntakeState;assistantMessage:string;currentQuestion:{id:string;fieldKey:string;tier:string;route:string;control:string;quickReplies:{label:string;value:unknown}[]} | null;proposedChanges?:{hash:string;profile:Profile};canShowPlans:boolean;provider_called:boolean};
export default function GuidedIntake({model,id}:{model:ReturnType<typeof useWizardProfile>;id:string}) {
  const [turn,setTurn]=useState<Turn>();const [text,setText]=useState('');const [exact,setExact]=useState('');const [permission,setPermission]=useState(false);const [busy,setBusy]=useState(false);const [notice,setNotice]=useState('');
  const controller=useRef<AbortController | null>(null);const navigate=useNavigate();
  async function load(action='read',value?:unknown) {
    controller.current?.abort();const abort=new AbortController();controller.current=abort;setBusy(true);setNotice('');
    try{const current=await model.flush();const data=await journey<Turn>('/intake/turn',{action,expected_revision:current.draft_revision,value,text,proposal_hash:turn?.proposedChanges?.hash,external_processing_consent:permission},'POST',{signal:abort.signal});if(abort.signal.aborted)return;setTurn(data);model.accept(data.state);setPermission(false);if(action!=='read' && action!=='clarify')setText('');setExact('');if(data.currentQuestion && data.currentQuestion.route!==id && ['direct','confirm','skip'].includes(action))track('step_complete',id,'chat');if(data.currentQuestion && data.currentQuestion.route!==id)navigate(pathFor(data.currentQuestion.route),{replace:true});}
    catch(e){if(!abort.signal.aborted)setNotice(e instanceof Error?e.message:'Try again.');}finally{if(!abort.signal.aborted)setBusy(false);}
  }
  useEffect(()=>{void load();return()=>controller.current?.abort();},[id]); // Read the server-owned question after route changes.
  const question=turn?.currentQuestion;
  if(question && question.route!==id)return <p role="status">Opening your next question…</p>;
  function direct() {if(!question)return;const field=question.fieldKey;const p=model.draft!;let value:unknown;
    if(field==='people'){const missing=p.people.findIndex(person=>person.age_years===null && !person.date_of_birth);value=missing>=0?p.people.map((person,index)=>index===missing?{...person,age_years:Number(exact),date_of_birth:null}:person):[{relationship:'lead_adult',age_years:Number(exact)}];}
    else if(field==='cover')value={...p.cover,start_date:exact};
    else if(field==='budget')value={choice:'amount',monthly_pence:Math.round(Number(exact)*100),strict:false};
    else if(question.id==='outpatient')value=Math.round(Number(exact)*100);
    else value=exact;void load('direct',value);
  }
  return <div className="w-guided" aria-busy={busy}><p className="uk-eyebrow">GUIDED INTAKE · {turn?.provider_called?'REVIEWED PROVIDER EXTRACTION':'DETERMINISTIC FALLBACK'}</p><div className="w-question" role="status"><p>{turn?.assistantMessage || 'Opening your next question…'}</p>{question?.tier==='Optional' && <p>Optional. Skip any time, or show your plans now.</p>}</div>
    {question && <><div className="w-options">{question.quickReplies.map(option=><button key={option.label} disabled={busy} onClick={()=>void load('direct',option.value)}>{option.label}</button>)}</div>{['people','cover','budget'].includes(question.fieldKey) && <form onSubmit={e=>{e.preventDefault();direct();}}><label className="j-field">{question.fieldKey==='people'?'Exact adult age':question.fieldKey==='cover'?'Exact start date':'Monthly budget in pounds'}<input type={question.fieldKey==='cover'?'date':'number'} min={question.fieldKey==='people'?18:0} max={question.fieldKey==='people'?85:10000} step={question.fieldKey==='budget'?'0.01':'1'} value={exact} onChange={e=>setExact(e.target.value)} required/></label><button disabled={busy || !exact}>Use this answer</button></form>}<form onSubmit={e=>{e.preventDefault();void load('propose');}}><label className="j-field">Your answer<textarea rows={3} value={text} maxLength={2000} onChange={e=>setText(e.target.value)} placeholder="A short answer, or ask for help. No identifying or diagnosis details."/></label><label className="j-check"><input type="checkbox" checked={permission} onChange={e=>setPermission(e.target.checked)}/> For this message only, allow the configured AI provider to process my answer. Otherwise use the local extractor.</label><div className="w-options"><button disabled={busy || !text.trim()}>Review captured answer</button><button type="button" disabled={busy} onClick={()=>void load('clarify')}>Explain this question</button>{question.tier==='Optional' && <button type="button" disabled={busy} onClick={()=>void load('skip')}>Skip this question</button>}</div></form></>}
    {turn?.proposedChanges && <section className="j-panel" aria-label="Review proposed answer"><h2>Is this what you meant?</h2><ProfileSummary profile={turn.proposedChanges.profile}/><details><summary>All proposed fields</summary><pre>{JSON.stringify(turn.proposedChanges.profile,null,2)}</pre></details><button disabled={busy} onClick={()=>void load('confirm')}>Confirm this answer</button><button onClick={()=>setTurn({...turn,proposedChanges:undefined})}>Edit my answer</button></section>}
    <div className="w-options"><button disabled={busy || (model.state?.version || 0)<2} onClick={()=>void load('undo')}>Undo last answer</button>{busy && <button onClick={()=>{controller.current?.abort();setBusy(false);setNotice('Stopped waiting. Refresh the current question before continuing.');}}>Stop</button>}<button disabled={busy} onClick={()=>void load()}>Refresh current question</button></div>{notice && <p className="j-error" role="alert">{notice}<button disabled={busy} onClick={()=>void load()}>Retry</button></p>}<details><summary>What we understand · version{model.state?.version}</summary><ProfileSummary profile={model.draft!}/></details><p>General information only. Existing conditions are never assumed covered. <Link to={pathFor('consent')}>Review processing permission</Link>.</p>
  </div>;
}
