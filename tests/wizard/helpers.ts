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
