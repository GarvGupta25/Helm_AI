import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Modal } from '../../ui/primitives';
import { journey, money } from '../api';
import type { Comparison, PlanItem } from '../Recommendations';
import PolicyQuestions from '../PolicyQuestions';

type Explanation={sections:{id:string;title:string;paragraphs:string[];sources:string[]}[];numbers:object};
export default function PlanDetail({item,result,selected,busy,onChoose,onSelect}:{item:PlanItem;result:Comparison;selected:string[];busy:boolean;onChoose:()=>void;onSelect:()=>void}) {
 const [data,setData]=useState<Explanation>();const [error,setError]=useState('');const [retry,setRetry]=useState(0);const [chat,setChat]=useState(false);
 useEffect(()=>{let active=true;void journey<Explanation>(`/runs/${result.run_id}/plans/${encodeURIComponent(item.id)}/explanation`).then(value=>{if(active)setData(value);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[item.id,result.run_id,retry]);
 return <><Link to="/get-cover/plans">← Back to plans and filters</Link><div className="w-detail-heading"><div><p className="j-badge">FICTIONAL INSURER {item.plan.insurer_id}</p><h2>{item.plan.name}</h2><p>Profile version{result.profile_version} · synthetic snapshot{item.plan.version}</p></div><div><p className="j-price">{money(item.quote.monthly_pence)} /month</p><button disabled={busy || !selected.includes(item.id) && selected.length>=3} onClick={onSelect}>Select this plan</button><label className="j-check"><input type="checkbox" checked={selected.includes(item.id)} disabled={busy || !selected.includes(item.id) && selected.length>=3} onChange={onChoose}/> Compare this plan</label><button onClick={()=>setChat(true)}>Ask about this plan</button></div></div>
 {error && <p role="alert">{error}<button onClick={()=>{setError('');setRetry(retry+1);}}>Retry explanation</button></p>}{!data && !error && <p role="status">Preparing the frozen policy explanation…</p>}<div className="w-detail-sections">{data?.sections.map(section=><section key={section.id} id={'plan-'+section.id}><h2>{section.title}</h2>{section.paragraphs.map((p,i)=><p key={i}>{p}</p>)}<small className="j-citations">Sources: {section.sources.join(' · ')}</small></section>)}</div>{data && <details><summary>Show the numbers</summary><p>Research scores are synthetic hypotheses, not regulated suitability assessments. Bands: excellent≥90%, strong75–89%, fair55–74%, limited below55% of component maximum.</p><pre>{JSON.stringify(data.numbers,null,2)}</pre></details>}<p>General information, not personal advice. No real cover is sold.</p>
 <Modal open={chat} onClose={()=>setChat(false)} title="Ask about this plan"><div className="journey"><PolicyQuestions item={item} runId={result.run_id} onClose={()=>setChat(false)}/></div></Modal>
 </>;
}
