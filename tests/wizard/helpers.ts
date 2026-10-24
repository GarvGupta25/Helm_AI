import { expect, type Page } from '@playwright/test';
export async function seedIntake(page:Page) {
 await page.goto('/get-cover/quote');await expect(page.getByRole('heading',{name:'A little clarity. One step at a time.'})).toBeVisible();
 await page.evaluate(async()=>{
  const headers={'Content-Type':'application/json','X-Journey-Session':sessionStorage.getItem('helm-journey') || ''};
  const state=await (await fetch('/api/journey/profile',{headers})).json();const date=new Date();date.setDate(date.getDate()+1);
  const profile={...state.draft,people:[{relationship:'lead_adult',age_years:35}],location:{region:'England'},cover:{start_date:date.toISOString().slice(0,10),underwriting_required:false},budget:{choice:'no_target',monthly_pence:null,strict:false},excess:{choice:'no_preference',max_pence:null,strict:false},hospital_list:{choice:'no_preference',minimum_tier:null},benefits:{required:[],preferred:[]}};
  const saved=await (await fetch('/api/journey/intake/draft',{method:'PATCH',headers,body:JSON.stringify({expected_revision:state.draft_revision,profile})})).json();
  const result=await fetch('/api/journey/profile/confirm',{method:'POST',headers,body:JSON.stringify({expected_version:saved.version,draft_hash:saved.draft_hash})});if(!result.ok)throw new Error('Fixture confirmation failed');
 });
}
export async function seedSelection(page:Page,count=1) {
 await seedIntake(page);
 await page.evaluate(async(count)=>{
  const headers={'Content-Type':'application/json','X-Journey-Session':sessionStorage.getItem('helm-journey') || ''};
  const run=await(await fetch('/api/journey/recommendations?limit=10',{method:'POST',headers,body:'{}'})).json();const items=run.items.slice(0,count);
  const consent=await(await fetch('/api/journey/consents',{method:'POST',headers,body:JSON.stringify({purpose:'insurer_share',recipients:[...new Set(items.map((item:{plan:{insurer_id:string}})=>item.plan.insurer_id))],accepted:true,wording_version:'journey-sharing-v1'})})).json();
  const response=await fetch('/api/journey/selection',{method:'POST',headers,body:JSON.stringify({run_id:run.run_id,expected_version:run.profile_version,plan_ids:items.map((item:{id:string})=>item.id),insurer_consent_id:consent.id})});if(!response.ok)throw new Error('Fixture selection failed');
 },count);
}
export async function seedVerified(page:Page,count=1) {
 await seedSelection(page,count);
 await page.evaluate(async()=>{
  const headers={'Content-Type':'application/json','X-Journey-Session':sessionStorage.getItem('helm-journey') || ''};
  const response=await fetch('/api/journey/verify/start',{method:'POST',headers,body:JSON.stringify({channel:'email',country_code:'+44',number:`access-${Date.now()}@example.test`,consent:true})});if(!response.ok)throw new Error('Fixture verification start failed');
  const {code}=await(await fetch('/api/journey/verify/demo-code',{headers})).json();const verified=await fetch('/api/journey/verify/check',{method:'POST',headers,body:JSON.stringify({code})});if(!verified.ok)throw new Error('Fixture verification failed');
 });
}
