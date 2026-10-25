import {test,expect} from '@playwright/test';
import {seedIntake} from './helpers';
import AxeBuilder from '@axe-core/playwright';

test.beforeEach(async({page})=>{
  await page.addInitScript(()=>localStorage.setItem('helm-cookie-consent-v1',JSON.stringify({necessary:true})));
});

for(const [step,benefit] of [['hospital','inpatient'],['wellbeing','mental health'],['everyday','dental']]) {
  test(`${step}: enable priorities here, switch all three options and restore saved choice`,async({page})=>{
    if(step==='wellbeing')await page.setViewportSize({width:375,height:900});
    await seedIntake(page);
    await page.goto('/get-cover/quote/benefits/'+step);
    const group=page.getByRole('group',{name:benefit+' priority',exact:true});
    await expect(group.getByRole('button',{name:'Nice to have',exact:true})).toBeDisabled();
    const permission=page.getByRole('button',{name:'I agree — enable health preferences',exact:true});
    await expect(permission).toBeVisible();
    if(step==='wellbeing'){
      await page.screenshot({path:'.runtime/benefit-permission-mobile.png',fullPage:true});
      const scan=await new AxeBuilder({page}).include('.wizard').analyze();
      expect(scan.violations.filter(v=>['serious','critical'].includes(v.impact || ''))).toEqual([]);
    }
    await permission.click();
    await expect(group.getByRole('button',{name:'Nice to have',exact:true})).toBeEnabled();
    for(const name of ['Nice to have','This is a must','No preference','This is a must']){
      await group.getByRole('button',{name,exact:true}).click();
      await expect(group.getByRole('button',{name,exact:true})).toHaveAttribute('aria-pressed','true');
      await expect(group.locator('[aria-pressed="true"]')).toHaveCount(1);
    }
    await expect(page.getByRole('status').filter({hasText:'Saved in your private session.'})).toBeVisible();
    await page.reload();
    await expect(group.getByRole('button',{name:'This is a must',exact:true})).toHaveAttribute('aria-pressed','true');
    await expect(group.getByRole('button',{name:'Nice to have',exact:true})).toBeEnabled();
    await page.getByRole('link',{name:'Review or withdraw processing permission',exact:true}).click();
    await page.getByRole('button',{name:'Continue without',exact:true}).click();
    await expect(page.getByText('You can continue without health-related answers and explicitly choose no essential benefits.',{exact:true})).toBeVisible();
    await page.goto('/get-cover/quote/benefits/'+step);
    await expect(group.getByRole('button',{name:'No preference',exact:true})).toHaveAttribute('aria-pressed','true');
    await expect(permission).toBeVisible();
  });
}

test('failed permission save keeps preferences locked, shows error and allows retry',async({page})=>{
  await seedIntake(page);
  await page.goto('/get-cover/quote/benefits/wellbeing');
  await page.route('**/api/journey/health-consent',route=>route.fulfill({status:503,json:{message:'Permission could not be saved. Retry.'}}),{times:1});
  const permission=page.getByRole('button',{name:'I agree — enable health preferences',exact:true});
  await permission.click();
  await expect(page.getByRole('alert')).toContainText('Permission could not be saved');
  const mental=page.getByRole('group',{name:'mental health priority',exact:true});
  await expect(mental.getByRole('button',{name:'This is a must',exact:true})).toBeDisabled();
  await permission.click();
  await expect(mental.getByRole('button',{name:'This is a must',exact:true})).toBeEnabled();
  await mental.getByRole('button',{name:'Nice to have',exact:true}).click();
  const physio=page.getByRole('group',{name:'physio priority',exact:true});
  await physio.getByRole('button',{name:'This is a must',exact:true}).click();
  await expect(mental.getByRole('button',{name:'Nice to have',exact:true})).toHaveAttribute('aria-pressed','true');
  await expect(physio.getByRole('button',{name:'This is a must',exact:true})).toHaveAttribute('aria-pressed','true');
});
