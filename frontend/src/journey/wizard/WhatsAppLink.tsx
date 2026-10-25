import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { journey } from '../api';

type Delivery = { delivery_status: string; expires_at: string; expired?: boolean; notice: string };
const messages: Record<string,string> = {
  pending:'Link submission is pending.', accepted:'The provider accepted your message. Delivery is not yet confirmed.',
  queued:'Your message is queued.', sending:'Your message is being sent.', sent:'The provider sent your message. Delivery is not yet confirmed.',
  delivered:'The provider confirmed delivery. Open the link on WhatsApp.', read:'The provider confirmed your message was read.',
  blocked:'Trial restrictions prevent this message. Your number is verified, but the link was not sent.',
  failed:'The provider could not confirm delivery.', undelivered:'The provider reported that the message was not delivered.',
  mock:'Developer simulation: no external message was sent.',
};

export default function WhatsAppLink(){
  const [data,setData]=useState<Delivery>(); const [error,setError]=useState('');
  const [mock,setMock]=useState(false); const [url,setUrl]=useState(''); const [busy,setBusy]=useState(false);
  useEffect(()=>{
    let active=true;
    async function refresh(){try{const value=await journey<Delivery>('/verify/magic-link');if(active)setData(value);}catch(e){if(active)setError(e instanceof Error?e.message:'Unable to check your link.');}}
    void refresh(); void journey<{mock?:boolean}>('/verify/config').then(c=>{if(active)setMock(Boolean(c.mock));});
    const timer=setInterval(()=>{void refresh();},4000);
    return()=>{active=false;clearInterval(timer);};
  },[]);
  async function prepare(){setBusy(true);setError('');try{setData(await journey<Delivery>('/verify/magic-link',{}));}catch(e){setError(e instanceof Error?e.message:'Unable to prepare your link.');}finally{setBusy(false);}}
  return <section className="uk-section journey wizard"><p className="uk-eyebrow">PRIVATE WHATSAPP ACCESS</p>
    <h1>Your verification and private link.</h1>
    {error && <p role="alert" className="j-error">{error}</p>}
    {data?<><p>Your WhatsApp verification succeeded.</p><p role="status">{data.expired?'This link expired. Verify again to request a new one.':messages[data.delivery_status] || data.notice}</p>
      <p>{data.notice}</p><p>Single-use link expires {new Date(data.expires_at).toLocaleString()}. Opening the link shows a confirmation screen before sign-in.</p>
      {mock && !data.expired && <button disabled={busy} onClick={()=>{setBusy(true);void journey<{url:string}>('/verify/mock-link').then(r=>setUrl(r.url)).catch(e=>setError(e.message)).finally(()=>setBusy(false));}}>Open private developer inbox</button>}
      {url && <p><a referrerPolicy="no-referrer" className="uk-button primary" href={url}>Open simulated sign-in link</a></p>}</>:<button disabled={busy} onClick={()=>void prepare()}>Prepare verified link</button>}
    <p><Link to="/get-cover/verify">Verify again or change number</Link></p><p><Link to="/my-quotes">Open an existing dashboard session</Link></p>
  </section>;
}
