import { useCallback, useEffect, useRef, useState } from 'react';
import { journey, openJourney, type IntakeState, type Profile } from '../api';

export function useWizardProfile() {
  const [state,setState] = useState<IntakeState>(); const [draft,setDraft] = useState<Profile>();
  const [error,setError] = useState(''); const [saving,setSaving] = useState(false); const [saved,setSaved] = useState(true);
  const [expired,setExpired] = useState(false);
  const current = useRef<Profile | undefined>(undefined); const remote = useRef<IntakeState | undefined>(undefined); const pending = useRef<Promise<IntakeState> | null>(null);
  const opening = useRef<Promise<IntakeState> | null>(null); const alive = useRef(true);
  const accept = useCallback((data: IntakeState) => { remote.current=data; current.current=data.draft; setState(data); setDraft(data.draft); setSaved(true); },[]);
  useEffect(() => { alive.current=true; opening.current ||= openJourney(); void opening.current.then(data=>{if(alive.current) accept(data);}).catch(e=>{if(alive.current){setError(e.message);setExpired([404,410].includes(e.status));}}); return()=>{alive.current=false;}; },[accept]);
  const flush = useCallback(async (): Promise<IntakeState> => {
    if (pending.current) await pending.current;
    if (!remote.current || !current.current) throw new Error('Your private intake is still opening.');
    if (JSON.stringify(remote.current.draft)===JSON.stringify(current.current)) return remote.current;
    setSaving(true); setError('');
    const task = (async()=>{
      while (JSON.stringify(remote.current!.draft)!==JSON.stringify(current.current)) {
        const snapshot=current.current!;
        const next=await journey<IntakeState>('/intake/draft',{expected_revision:remote.current!.draft_revision,profile:snapshot},'PATCH');
        remote.current=next; if(alive.current)setState(next);
        if(current.current===snapshot){current.current=next.draft;if(alive.current)setDraft(next.draft);}
      }
      if(alive.current)setSaved(true); return remote.current!;
    })();
    pending.current=task;
    try{return await task;}catch(e){if(alive.current)setError(e instanceof Error?e.message:'Could not save. Try again.');throw e;}finally{pending.current=null;if(alive.current)setSaving(false);}
  },[]);
  useEffect(()=>{if(!draft || saved)return;const timer=setTimeout(()=>{void flush().catch(()=>{});},450);return()=>clearTimeout(timer);},[draft,saved,flush]);
  useEffect(()=>{const warn=(event:BeforeUnloadEvent)=>{if(current.current && remote.current && JSON.stringify(current.current)!==JSON.stringify(remote.current.draft)){event.preventDefault();event.returnValue='';}};window.addEventListener('beforeunload',warn);return()=>window.removeEventListener('beforeunload',warn);},[]);
  function change<K extends keyof Profile>(key: K,value:Profile[K]) { if(!current.current)return;const next={...current.current,[key]:value};current.current=next;setDraft(next);setSaved(false);setError(''); }
  async function confirm(source:'manual'|'guided_chat'='manual') {const data=await flush();if(data.version && JSON.stringify(data.profile)===JSON.stringify(data.draft))return data;const next=await journey<IntakeState>('/profile/confirm',{expected_version:data.version,draft_hash:data.draft_hash,source});accept(next);return next;}
  async function consent(accepted:boolean) {await flush();accept(await journey<IntakeState>('/health-consent',{accepted}));}
  async function restart(){setError('');accept(await openJourney(true));setExpired(false);}
  return {state,draft,error,saving,saved,expired,restart,change,flush,confirm,consent,accept,setError};
}
