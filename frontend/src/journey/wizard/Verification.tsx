import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { journey } from '../api';
import type { SelectionReceipt } from './SelectionReview';
import BrokerContact from './BrokerContact';
import '../journey.css';
import './wizard.css';

type Status = { contact_id: string; channel: string; mode: string; verified: boolean; attempts_left: number; resend_after: number; expires_at: string };
type Config = { mock?: boolean; automatic_link?: boolean; mode: string; real_delivery: boolean; channels: { whatsapp: boolean; email: boolean } };
export default function Verification() {
  const codePage=useLocation().pathname.endsWith('/code'); const navigate=useNavigate();
  const [receipt,setReceipt]=useState<SelectionReceipt>(); const [status,setStatus]=useState<Status>(); const [config,setConfig]=useState<Config>();
  const [channel,setChannel]=useState<'whatsapp'|'email'>('whatsapp'); const [country,setCountry]=useState('+44'); const [custom,setCustom]=useState('+');
  const [number,setNumber]=useState(''); const [permission,setPermission]=useState(false); const [digits,setDigits]=useState(['','','','','','']);
  const [demoCode,setDemoCode]=useState('');
  const [busy,setBusy]=useState(false); const [error,setError]=useState(''); const [remaining,setRemaining]=useState(0); const refs=useRef<(HTMLInputElement|null)[]>([]);
  async function refresh() { const value=await journey<Status>('/verify/status');setStatus(value);setRemaining(value.resend_after);return value; }
  useEffect(()=>{
    let active=true;
    void journey<SelectionReceipt>('/selection').then(value=>{if(active)setReceipt(value);}).catch(e=>{if(active)setError(e.message);});
    void journey<Config>('/verify/config').then(value=>{if(active)setConfig(value);}).catch(()=>{if(active)setError('Verification is currently unavailable. Please try again later.');});
    if(codePage) void refresh().then(value=>{
      if(active && value.mode==='console'){setStatus(undefined);setError('Please request a new WhatsApp code.');navigate('/get-cover/verify',{replace:true});}
    }).catch(()=>{if(active){setStatus(undefined);navigate('/get-cover/verify',{replace:true});}});
    return()=>{active=false;};
  },[codePage,navigate]);
  useEffect(()=>{if(remaining<=0)return;const timer=setTimeout(()=>setRemaining(value=>Math.max(0,value-1)),1000);return()=>clearTimeout(timer);},[remaining]);
  useEffect(()=>{if(codePage && status)refs.current[0]?.focus();},[codePage,status?.contact_id]);
  useEffect(()=>{
    let active=true;setDemoCode('');
    if(codePage && config?.mock && status?.contact_id)void journey<{code:string}>('/verify/demo-code').then(r=>{if(active)setDemoCode(r.code);}).catch(e=>{if(active)setError(e.message);});
    return()=>{active=false;};
  },[codePage,config?.mock,status?.contact_id]);
  async function perform(action:()=>Promise<void>) {
    setBusy(true);setError('');
    try{await action();}catch(e){setError(e instanceof Error?e.message:'Please try again.');if(codePage)void refresh().catch(()=>{});}finally{setBusy(false);}
  }
  async function send() {
    await journey('/verify/start',{country_code:country==='custom'?custom:country,number,channel,consent:true,wording_version:'contact-verification-v1'});
    setDigits(['','','','','','']);await refresh();navigate('/get-cover/verify/code');
  }
  function enter(index:number,value:string) {
    const clean=value.replace(/\D/g,'').slice(0,6);
    if(clean.length>1){const next=[...digits];for(let offset=0;offset<clean.length && index+offset<6;offset++)next[index+offset]=clean[offset];setDigits(next);refs.current[Math.min(5,index+clean.length)]?.focus();}
    else{setDigits(digits.map((digit,i)=>i===index?clean:digit));if(clean && index<5)refs.current[index+1]?.focus();}
  }
  const currentChannel=codePage && status?status.channel:channel;
  const serviceReady=Boolean((config?.real_delivery || config?.mock) && config?.channels?.[channel]);
  const validCodePage=codePage && status && status.mode!=='console';
  return <section className="uk-section journey wizard">
    <nav className="w-progress" aria-label="Private quote access"><ol>{['Verify','Your link','Your quotes'].map((label,i)=><li key={label} aria-current={i===0?'step':undefined}><span>{i+1}</span>{label}</li>)}</ol></nav>
    {config?.mock && <p className="j-notice" role="status">Demo only. No WhatsApp message is sent and this does not verify ownership of a phone number.</p>}
    <p className="uk-eyebrow">PRIVATE ACCESS · {config?.mock?'WHATSAPP DEMO':currentChannel==='whatsapp'?'WHATSAPP VERIFICATION':'EMAIL VERIFICATION'}</p>
    <h1>{config?.mock?(codePage?'Enter your demo code.':'Try WhatsApp demo login.'):codePage?(currentChannel==='whatsapp'?'Check your WhatsApp.':'Check your email.'):'Verify your WhatsApp number.'}</h1>
    <p>{config?.mock?(codePage?'Use the six-digit demo OTP shown below to continue to your private quotation link.':'Enter a phone number in the correct format. We will generate a demo OTP here, so you can try the quotation journey without receiving a message.'):codePage?'Enter the six-digit code from your selected channel. It may take a moment to arrive.':'Use your actual WhatsApp number. We will send a six-digit code to confirm it belongs to you. No insurance or medical information is included in the message.'}</p>
    {error && <p role="alert" className="j-error">{error}</p>}
    {!receipt?<p><Link to="/get-cover/selection">Review your selection before verification.</Link></p>:validCodePage?<>
      <p>Expires {new Date(status.expires_at).toLocaleTimeString()}. {status.attempts_left} attempts left.</p>
      {config?.mock && demoCode && <div className="j-notice"><p>Demo OTP: <output aria-label="Demo OTP">{demoCode}</output></p><button disabled={busy} onClick={()=>{setDigits(demoCode.split(''));refs.current[0]?.focus();}}>Use demo OTP</button></div>}
      <form onSubmit={event=>{event.preventDefault();void perform(async()=>{await journey('/verify/check',{code:digits.join('')});navigate('/get-cover/access');});}}>
        <div className="w-code" role="group" aria-label="Six-digit verification code" dir="ltr">{digits.map((digit,index)=><input key={index} ref={element=>{refs.current[index]=element;}} type="text" inputMode="numeric" autoComplete={index===0?'one-time-code':'off'} aria-label={`Code digit ${index+1}`} value={digit} maxLength={6} onChange={event=>enter(index,event.target.value)} onPaste={event=>{event.preventDefault();enter(index,event.clipboardData.getData('text'));}} onKeyDown={event=>{if(event.key==='Backspace' && !digit && index>0)refs.current[index-1]?.focus();if(event.key==='ArrowLeft' && index>0)refs.current[index-1]?.focus();if(event.key==='ArrowRight' && index<5)refs.current[index+1]?.focus();}}/>)}</div>
        <button className="uk-button primary" disabled={busy || digits.join('').length!==6 || status.attempts_left===0}>Verify and continue</button>
      </form>
      <p role="status">{remaining?`You can request another code in ${remaining} seconds.`:'You can request another code now.'}</p>
      <button disabled={busy || remaining>0} onClick={()=>void perform(async()=>{await journey('/verify/resend',{});setDigits(['','','','','','']);await refresh();})}>Resend code</button>
      <Link to="/get-cover/verify">Change number</Link>
    </>:codePage?<p role="status">Checking your verification request…</p>:<form className="w-step" onSubmit={event=>{event.preventDefault();void perform(send);}}>
      {config && !serviceReady && <p className="j-notice" role="status">{channel==='whatsapp'?'WhatsApp':'Email'} verification is currently unavailable. Please try again later or contact us for help.</p>}
      {!config && !error && <p role="status">Checking verification availability…</p>}
      {config?.channels?.email && <div className="w-options" role="group" aria-label="Verification channel"><button type="button" aria-pressed={channel==='whatsapp'} onClick={()=>{setChannel('whatsapp');setNumber('');setPermission(false);}}>WhatsApp</button><button type="button" aria-pressed={channel==='email'} onClick={()=>{setChannel('email');setNumber('');setPermission(false);}}>Use email instead</button></div>}
      {channel==='whatsapp' && <><label className="j-field">Country calling code<select aria-label="Country calling code" value={country} onChange={event=>setCountry(event.target.value)}>{[['+44','United Kingdom +44'],['+91','India +91'],['+1','United States / Canada +1'],['+61','Australia +61'],['+33','France +33'],['+49','Germany +49'],['custom','Another country code']].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>{country==='custom' && <label className="j-field">International calling code<input inputMode="tel" value={custom} maxLength={4} onChange={event=>setCustom(event.target.value)} placeholder="+"/></label>}</>}
      <label className="j-field">{channel==='whatsapp'?'WhatsApp number':'Email address'}<input type={channel==='email'?'email':'tel'} autoComplete={channel==='email'?'email':'tel-national'} value={number} maxLength={180} onChange={event=>setNumber(event.target.value)} required minLength={channel==='whatsapp'?7:3} placeholder={channel==='email'?'Your email address':'Your WhatsApp number'}/></label>
      <label className="j-check"><input type="checkbox" checked={permission} onChange={event=>setPermission(event.target.checked)}/> {config?.mock?'I agree to use this number for the demo verification and private quotation journey. No WhatsApp messages will be sent.':'I agree to receive a verification code and a single-use sign-in link on this selected channel for my private quotation access. This does not opt me into marketing or quotation reminders.'}</label>
      <button className="uk-button primary" disabled={busy || !serviceReady || !permission || !number || remaining>0}>{busy?(config?.mock?'Generating demo OTP…':'Sending your code…'):config?.mock?'Generate demo OTP':channel==='whatsapp'?'Send WhatsApp OTP':'Send code by email'}</button>
      {remaining>0 && <p role="status">Wait {remaining} seconds before sending another code.</p>}
    </form>}
    <div className="w-tools"><button type="button" onClick={()=>window.dispatchEvent(new Event('helm-open-assistant'))}>Ask Helm</button><Link to="/get-cover/selection">Back to selection</Link><Link to="/contact">Contact us</Link></div>
    <BrokerContact docked/>
  </section>;
}
