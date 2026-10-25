import {test,expect} from '@playwright/test';
import {seedIntake} from './helpers';
for(const width of [1440,375])test(`compare and consented selection at ${width}px`,async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('helm-cookie-consent-v1',JSON.stringify({necessary:true})));await page.setViewportSize({width,height:900});await seedIntake(page);await page.goto('/get-cover/plans');await expect(page.locator('.w-plan-card')).toHaveCount(10);
 for(let i=0;i<2;i++)await page.locator('.w-plan-card').nth(i).getByRole('checkbox').check();await page.getByRole('link',{name:'Compare choices',exact:true}).click();await expect(page.getByRole('heading',{name:'Main differences'})).toBeVisible();await expect(page.getByText(/has the lowest monthly premium here/)).toBeVisible();
 await page.getByRole('button',{name:'Select this plan',exact:true}).first().click();await expect(page.getByRole('heading',{name:'Review your choice'})).toBeVisible();await expect(page.getByRole('button',{name:'Request my quotes'})).toBeDisabled();await page.getByRole('checkbox',{name:/I explicitly consent to share this reviewed fictional profile/}).check();await page.getByRole('button',{name:'Request my quotes'}).click();await expect(page).toHaveURL(/\/get-cover\/verify$/);
 await page.goto('/get-cover/selection');await expect(page.getByText('Selection saved only.',{exact:false})).toBeVisible();await expect(page.getByRole('link',{name:'Continue to verification'})).toBeVisible();
});
