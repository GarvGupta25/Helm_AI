import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
test.beforeEach(async({page})=>{await page.addInitScript(()=>localStorage.setItem('helm-cookie-consent-v1',JSON.stringify({necessary:true})));});
test('shell mode choice, deep-link guard and flag-off fallback',async({page})=>{
 await page.goto('/get-cover/quote'); await expect(page.getByRole('heading',{name:'A little clarity. One step at a time.'})).toBeVisible();
 await page.getByRole('button',{name:'Fill it in myself',exact:false}).click();await expect(page).toHaveURL(/\/consent$/);
 await page.goto('/get-cover/quote/review');await expect(page).toHaveURL(/\/people$/);
 await page.reload();await expect(page.getByRole('heading',{name:'Who needs cover?'})).toBeVisible();
 await page.getByRole('button',{name:'Switch to guided chat'}).click();await expect(page.getByRole('button',{name:'Switch to the form'})).toBeVisible();
 const result=await new AxeBuilder({page}).include('.wizard').analyze();expect(result.violations.filter(v=>['serious','critical'].includes(v.impact || ''))).toEqual([]);
 await page.goto('http://127.0.0.1:4174/get-cover/quote');await expect(page.getByRole('heading',{name:'Find cover that fits your needs.'})).toBeVisible();
});
