import {test,expect} from '@playwright/test';
import {seedIntake} from './helpers';
for(const width of [1440,375])test(`optional steps can all be skipped at ${width}px`,async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('helm-cookie-consent-v1',JSON.stringify({necessary:true})));await page.setViewportSize({width,height:900});await seedIntake(page);
 await page.goto('/get-cover/quote/optional/existing-cover');await expect(page.getByRole('button',{name:'Show my plans',exact:true})).toBeEnabled();
 for(const topic of ['existing-cover','underwriting','outpatient','postcode','conditions']){await expect(page).toHaveURL(new RegExp('/optional/'+topic+'$'));await page.getByRole('button',{name:'Skip',exact:true}).click();await expect(page).not.toHaveURL(new RegExp('/optional/'+topic+'$'));}
 await expect(page.getByRole('heading',{name:'Check your answers.'})).toBeVisible();
 await page.getByRole('link',{name:'Edit existing cover',exact:true}).click();await page.getByRole('button',{name:'Switching',exact:true}).click();await page.getByRole('button',{name:'Next',exact:true}).click();await expect(page).toHaveURL(/\/review$/);
 await page.getByRole('button',{name:'Show my plans',exact:true}).click();await expect(page).toHaveURL(/\/get-cover\/plans$/);
 await page.goto('/get-cover/quote/review');await page.getByRole('button',{name:'Undo confirmed change'}).click();await expect(page.getByText('Existing cover: Not answered',{exact:false})).toBeVisible();
 await page.getByText('Confirmed profile history',{exact:true}).click();await page.getByRole('button',{name:'Load confirmed versions'}).click();await expect(page.getByText(/Version3/)).toBeVisible();
});
