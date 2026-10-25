import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { seedSelection } from './helpers';

for (const width of [1440, 375]) test(`Twilio trial blocked status, OTP paste and no developer secrets ${width}`, async({page})=>{
  await page.setViewportSize({width,height:900});
  await page.addInitScript(()=>localStorage.setItem('helm-cookie-consent-v1',JSON.stringify({necessary:true})));
  await seedSelection(page);
  let started=false;
  await page.route('**/api/journey/verify/**',async route=>{
    const path=new URL(route.request().url()).pathname;
    if(path.endsWith('/config'))return route.fulfill({json:{mode:'twilio',automatic_link:true,mock:false,real_delivery:true,channels:{whatsapp:true,email:false}}});
    if(path.endsWith('/start')){const body=route.request().postDataJSON();expect(body.number).toBe('9876543210');expect(body.country_code).toBe('+91');started=true;return route.fulfill({json:{delivery_status:'queued'}});}
    if(path.endsWith('/status'))return route.fulfill({status:started?200:404,json:{contact_id:'fixture',mode:'twilio',verified:false,channel:'whatsapp',attempts_left:5,resend_after:60,expires_at:new Date(Date.now()+600000).toISOString()}});
    if(path.endsWith('/check')){expect(route.request().postDataJSON().code).toBe('765432');return route.fulfill({json:{verified:true,magic_link:{delivery_status:'blocked'}}});}
    if(path.endsWith('/magic-link'))return route.fulfill({json:{delivery_status:'blocked',notice:'Trial restrictions prevent link delivery.',expires_at:new Date(Date.now()+600000).toISOString()}});
    throw new Error('Real provider UI must never retrieve developer codes or links.');
  });
  await page.goto('/get-cover/verify');
  await page.getByLabel('Country calling code',{exact:true}).selectOption('+91');
  await page.getByPlaceholder('Your WhatsApp number',{exact:true}).fill('9876543210');
  await page.getByRole('checkbox',{name:/I agree to receive a verification code/}).check();
  await page.getByRole('button',{name:'Send WhatsApp OTP',exact:true}).click();
  await expect(page.getByRole('button',{name:'Resend code',exact:true})).toBeDisabled();
  await page.getByRole('textbox',{name:'Code digit 1',exact:true}).fill('765432');
  await page.getByRole('button',{name:'Verify and continue',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Your verification and private link.'})).toBeVisible();
  await expect(page.getByRole('status')).toContainText('link was not sent');
  await expect(page.getByRole('button',{name:'Show demo sign-in link'})).toHaveCount(0);
  await expect(page.getByLabel('Demo OTP',{exact:true})).toHaveCount(0);
  await expect(page.locator('.wizard a[href*="#"]')).toHaveCount(0);
  const scan=await new AxeBuilder({page}).include('.wizard').analyze();
  expect(scan.violations.filter(v=>['serious','critical'].includes(v.impact || ''))).toEqual([]);
  await page.screenshot({path:`.runtime/twilio-blocked-${width}.png`,fullPage:true});
});

test('demo phone entry generates an OTP and preserves private link access',async({page})=>{
  await page.addInitScript(()=>localStorage.setItem('helm-cookie-consent-v1',JSON.stringify({necessary:true})));
  await seedSelection(page);
  await page.route('**/api/journey/verify/**',async route=>{
    const path=new URL(route.request().url()).pathname;
    if(path.endsWith('/config'))return route.fulfill({json:{mode:'mock',automatic_link:true,mock:true,real_delivery:false,channels:{whatsapp:true,email:false}}});
    if(path.endsWith('/start')){expect(route.request().postDataJSON().number).toBe('9876543210');return route.fulfill({json:{mode:'mock'}});}
    if(path.endsWith('/status'))return route.fulfill({json:{contact_id:'fixture',mode:'mock',verified:false,channel:'whatsapp',attempts_left:5,resend_after:60,expires_at:new Date(Date.now()+300000).toISOString()}});
    if(path.endsWith('/demo-code'))return route.fulfill({json:{code:'765432'}});
    if(path.endsWith('/check'))return route.fulfill({json:{verified:true,real_ownership_verified:false}});
    if(path.endsWith('/magic-link'))return route.fulfill({json:{delivery_status:'mock',notice:'Simulation only.',expires_at:new Date(Date.now()+600000).toISOString()}});
    if(path.endsWith('/mock-link'))return route.fulfill({json:{url:'/my-quotes#'+'x'.repeat(43)}});
    throw new Error('Unexpected request');
  });
  await page.goto('/get-cover/verify');
  await expect(page.getByText(/Demo only. No WhatsApp message/)).toBeVisible();
  await page.getByLabel('Country calling code',{exact:true}).selectOption('+91');
  await page.getByPlaceholder('Your WhatsApp number',{exact:true}).fill('9876543210');
  await page.getByRole('checkbox',{name:/I agree to use this number for the demo/}).check();
  await page.getByRole('button',{name:'Generate demo OTP',exact:true}).click();
  await expect(page.getByLabel('Demo OTP',{exact:true})).toHaveText('765432');
  await page.getByRole('button',{name:'Use demo OTP'}).click();
  await page.getByRole('button',{name:'Verify and continue',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Your verification and private link.'})).toBeVisible();
  await expect(page.getByRole('status')).toContainText('no external message');
  await expect(page.getByText('Your demo OTP was accepted. Phone ownership has not been verified.')).toBeVisible();
  await page.getByRole('button',{name:'Show demo sign-in link'}).click();
  await expect(page.getByRole('link',{name:'Continue to my quotes'})).toHaveAttribute('href','/my-quotes#'+'x'.repeat(43));
});
