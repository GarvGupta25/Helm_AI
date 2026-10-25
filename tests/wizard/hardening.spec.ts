import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {seedIntake} from './helpers';
test('keyboard, dark RTL structure and narrow reflow retain usable controls',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('helm-cookie-consent-v1',JSON.stringify({necessary:true,analytics:false})));
 await seedIntake(page);
 await page.goto('/get-cover/quote/region');
 await expect(page.getByRole('heading',{name:'Where do you live?'})).toBeFocused();
 await page.getByRole('button',{name:'England',exact:true}).focus();await page.keyboard.press('Space');
 await expect(page.getByRole('button',{name:'England',exact:true})).toHaveAttribute('aria-pressed','true');
 for(const width of [1440,375,320]){
  await page.setViewportSize({width,height:900});await page.emulateMedia({colorScheme:'dark',reducedMotion:'reduce'});
  await page.evaluate(()=>{document.documentElement.dir='rtl';});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  const assistant=await page.getByRole('button',{name:'Ask Helm',exact:true}).boundingBox();
  const broker=await page.getByRole('button',{name:'Talk to a broker',exact:true}).boundingBox();
  expect(assistant && broker && (assistant.y+assistant.height<=broker.y || broker.y+broker.height<=assistant.y)).toBeTruthy();
  const scan=await new AxeBuilder({page}).include('.wizard').analyze();expect(scan.violations.filter(v=>['serious','critical'].includes(v.impact||''))).toEqual([]);
  await expect(page.getByRole('button',{name:'Next',exact:true})).toBeVisible();
 }
 await page.evaluate(()=>{document.documentElement.dir='ltr';});
 await page.getByRole('button',{name:'Next',exact:true}).focus();await page.keyboard.press('Enter');
 await expect(page.getByRole('heading',{name:'When should cover start?'})).toBeFocused();
 await page.getByText('Your data and privacy',{exact:true}).click();
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export my journey',exact:true}).click();expect((await download).suggestedFilename()).toBe('helm-private-journey.json');
 await page.getByRole('checkbox',{name:/I understand deletion permanently/}).check();await page.getByRole('button',{name:'Delete my journey',exact:true}).click();await expect(page.getByRole('heading',{name:'A little clarity. One step at a time.'})).toBeVisible();
});
test('expired intake offers a fresh session instead of a reload loop',async({page})=>{
 await page.addInitScript(()=>{sessionStorage.setItem('helm-journey','x'.repeat(43));localStorage.setItem('helm-cookie-consent-v1',JSON.stringify({necessary:true}));});
 await page.route('**/api/journey/profile',route=>route.fulfill({status:410,json:{detail:'Your intake session expired. Start a new session.'}}));
 await page.goto('/get-cover/quote');await page.getByRole('button',{name:'Start a new private intake',exact:true}).click();
 await expect(page.getByRole('heading',{name:'A little clarity. One step at a time.'})).toBeVisible();
});
