import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {seedIntake} from './helpers';
for(const width of [1440,375])test(`plain-English detail and grounded questions at ${width}px`,async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('helm-cookie-consent-v1',JSON.stringify({necessary:true})));await page.setViewportSize({width,height:900});await seedIntake(page);await page.goto('/get-cover/plans');await expect(page.locator('.w-plan-card')).toHaveCount(10);await page.locator('.w-plan-card').first().getByRole('link',{name:'Details',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Why this plan fits you',exact:true})).toBeVisible();for(const title of ["What's covered","What's not covered","What you'll pay",'Conditions and waiting periods','Hospital access','How we estimate'])await expect(page.getByRole('heading',{name:title,exact:true})).toBeVisible();
 await expect(page.getByText('Show the numbers',{exact:true}).locator('..')).not.toHaveAttribute('open','');
 const scan=await new AxeBuilder({page}).include('.w-plans').analyze();expect(scan.violations.filter(v=>['serious','critical'].includes(v.impact || ''))).toEqual([]);
 await page.getByRole('button',{name:'Ask about this plan',exact:true}).click();const dialog=page.getByRole('dialog',{name:'Ask about this plan',exact:true});await dialog.getByRole('button',{name:'Break down my premium',exact:true}).click();await expect(dialog.getByRole('log')).toContainText('quote.monthly_pence');await dialog.getByRole('textbox',{name:'Ask about this policy',exact:true}).fill('Is worldwide care guaranteed?');await dialog.getByRole('button',{name:'Ask policy question',exact:true}).click();await expect(dialog.getByRole('log')).toContainText('no coverage or cost has been guessed');await dialog.getByRole('button',{name:'Close policy questions'}).click();
 await page.getByRole('link',{name:'← Back to plans and filters',exact:true}).click();await expect(page.locator('.w-plan-card')).toHaveCount(10);
});
