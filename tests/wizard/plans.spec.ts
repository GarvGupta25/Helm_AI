import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {seedIntake} from './helpers';
for(const width of [1440,375])test(`plans view filters and three-plan limit at ${width}px`,async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('helm-cookie-consent-v1',JSON.stringify({necessary:true})));await page.setViewportSize({width,height:900});await seedIntake(page);await page.goto('/get-cover/plans');
 await expect(page.locator('.w-plan-card')).toHaveCount(10);const version=await page.evaluate(async()=>{const r=await fetch('/api/journey/profile',{headers:{'X-Journey-Session':sessionStorage.getItem('helm-journey') || ''}});return(await r.json()).version;});
 for(let i=0;i<3;i++)await page.locator('.w-plan-card').nth(i).getByRole('checkbox').check();await expect(page.locator('.w-plan-card').nth(3).getByRole('checkbox')).toBeDisabled();
 const panel=width===375?page.getByRole('dialog',{name:'Refine your plan view'}):page.getByRole('complementary',{name:'Plan display filters'});if(width===375)await page.getByRole('button',{name:'Filters',exact:true}).click();await panel.getByLabel('Maximum monthly premium (£)',{exact:true}).fill('0');
 if(width===375)await panel.getByRole('button',{name:'Apply view filters'}).click();await expect(page.getByRole('heading',{name:'No plans in this view.'})).toBeVisible();
 const after=await page.evaluate(async()=>{const r=await fetch('/api/journey/profile',{headers:{'X-Journey-Session':sessionStorage.getItem('helm-journey') || ''}});return(await r.json()).version;});expect(after).toBe(version);
 await page.getByRole('button',{name:'Reset display filters',exact:true}).click();await expect(page.locator('.w-plan-card')).toHaveCount(10);
 const scan=await new AxeBuilder({page}).include('.w-plans').analyze();expect(scan.violations.filter(v=>['serious','critical'].includes(v.impact || ''))).toEqual([]);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:`.runtime/wizard-plans-${width}.png`,fullPage:true});
});
