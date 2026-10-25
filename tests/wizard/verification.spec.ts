import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {seedSelection} from './helpers';

test.beforeEach(async({page})=>{await page.addInitScript(()=>localStorage.setItem('helm-cookie-consent-v1',JSON.stringify({necessary:true})));});

for(const width of [1440,375])test(`WhatsApp verification uses the real-number flow at ${width}px`,async({page})=>{
 // UI fixture only. Actual provider payload/ownership enforcement is tested against FastAPI separately.
 await page.setViewportSize({width,height:900});await seedSelection(page);
 let started=false,checked=false;
 await page.route('**/api/journey/verify/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/config'))return route.fulfill({json:{mode:'whatsmcp',real_delivery:true,channels:{whatsapp:true,email:false}}});
  if(path.endsWith('/start')){const body=route.request().postDataJSON();expect(body.number).toBe('+12025550123');expect(body.channel).toBe('whatsapp');expect(body.consent).toBe(true);started=true;return route.fulfill({json:{delivery_status:'sent'}});}
  if(path.endsWith('/status'))return route.fulfill({status:started?200:404,json:started?{contact_id:'fixture-contact',channel:'whatsapp',mode:'whatsmcp',verified:checked,attempts_left:5,resend_after:60,expires_at:new Date(Date.now()+600000).toISOString()}:{detail:'Request a code first'}});
  if(path.endsWith('/check')){expect(route.request().postDataJSON().code).toBe('123456');checked=true;return route.fulfill({json:{verified:true,real_ownership_verified:true}});}
  throw new Error('The public verification UI must not request a local code.');
 });
 await page.goto('/get-cover/verify');
 await expect(page.getByRole('heading',{name:'Verify your WhatsApp number.'})).toBeVisible();
 await expect(page.locator('.wizard')).not.toContainText(/fictional|local simulation|private demo inbox/i);
 await page.getByLabel('Country calling code',{exact:true}).selectOption('+1');
 await page.getByPlaceholder('Your WhatsApp number',{exact:true}).fill('+12025550123');
 await expect(page.getByRole('button',{name:'Send code on WhatsApp',exact:true})).toBeDisabled();
 await page.getByRole('checkbox',{name:/I agree to receive a verification code/}).check();
 await page.getByRole('button',{name:'Send code on WhatsApp',exact:true}).click();
 await expect(page).toHaveURL(/\/verify\/code$/);await expect(page.getByRole('heading',{name:'Check your WhatsApp.'})).toBeVisible();
 await expect(page.getByRole('button',{name:'Reveal local demo code'})).toHaveCount(0);
 await page.screenshot({path:`.runtime/real-whatsapp-code-${width}.png`});
 const scan=await new AxeBuilder({page}).include('.wizard').analyze();expect(scan.violations.filter(v=>['serious','critical'].includes(v.impact || ''))).toEqual([]);
 await page.getByRole('textbox',{name:'Code digit 1',exact:true}).fill('123456');
 await expect(page.getByRole('textbox',{name:'Code digit 6',exact:true})).toHaveValue('6');
 await page.getByRole('button',{name:'Verify and continue',exact:true}).click();await expect(page).toHaveURL(/\/get-cover\/access$/);
 expect(started && checked).toBeTruthy();
});

test('missing credentials blocks sends without offering simulated codes',async({page})=>{
 await seedSelection(page);
 await page.route('**/api/journey/verify/config',route=>route.fulfill({json:{mode:'whatsmcp',real_delivery:false,channels:{whatsapp:false,email:false}}}));
 await page.goto('/get-cover/verify');await expect(page.getByText('WhatsApp verification is currently unavailable.',{exact:false})).toBeVisible();
 await page.getByPlaceholder('Your WhatsApp number',{exact:true}).fill('+12025550123');await page.getByRole('checkbox',{name:/I agree to receive a verification code/}).check();
 await expect(page.getByRole('button',{name:'Send code on WhatsApp',exact:true})).toBeDisabled();
 await expect(page.locator('.wizard')).not.toContainText(/fictional|local simulation|private demo inbox|reveal local/i);
 await page.screenshot({path:'.runtime/real-whatsapp-setup-required.png'});
});

test('old console-mode code page redirects to request actual verification',async({page})=>{
 await seedSelection(page);
 await page.evaluate(async()=>{const response=await fetch('/api/journey/verify/start',{method:'POST',headers:{'Content-Type':'application/json','X-Journey-Session':sessionStorage.getItem('helm-journey') || ''},body:JSON.stringify({channel:'email',number:'old-console@example.test',consent:true})});if(!response.ok)throw new Error('Console fixture setup failed');});
 await page.goto('/get-cover/verify/code');await expect(page).toHaveURL(/\/get-cover\/verify$/);
 await expect(page.getByPlaceholder('Your WhatsApp number',{exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Reveal local demo code'})).toHaveCount(0);
});
