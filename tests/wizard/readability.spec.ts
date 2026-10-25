import {test,expect,type Locator} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {seedVerified} from './helpers';

async function readable(card:Locator){
 const ratios=await card.locator('h2,h3,p,a,label').evaluateAll(elements=>elements.filter(element=>element.getClientRects().length).map(element=>{
  const rgb=(value:string)=>value.match(/[\d.]+/g)!.map(Number);
  const luminance=(value:number[])=>value.slice(0,3).map(n=>{const v=n/255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;}).reduce((sum,n,i)=>sum+n*[.2126,.7152,.0722][i],0);
  let node:Element|null=element;let background=[255,255,255];
  while(node){const candidate=rgb(getComputedStyle(node).backgroundColor);if(candidate.length===3 || candidate[3]===1){background=candidate;break;}node=node.parentElement;}
  const foreground=luminance(rgb(getComputedStyle(element).color)),back=luminance(background);
  return (Math.max(foreground,back)+.05)/(Math.min(foreground,back)+.05);
 }));
 expect(ratios.length).toBeGreaterThan(0);expect(Math.min(...ratios)).toBeGreaterThanOrEqual(4.5);
}

for(const width of [1440,375])test(`light forms and plan/dashboard cards stay readable in dark OS mode at ${width}px`,async({page})=>{
 await page.setViewportSize({width,height:960});await page.emulateMedia({colorScheme:'dark',reducedMotion:'reduce'});
 await page.addInitScript(()=>localStorage.setItem('helm-cookie-consent-v1',JSON.stringify({necessary:true})));
 await seedVerified(page,2);await page.goto('/get-cover/plans');
 const card=page.locator('.w-plan-card').first();await expect(card).toBeVisible();await readable(card);
 const details=card.getByRole('link',{name:'Details',exact:true});await details.hover();await readable(card);await details.focus();await readable(card);
 expect(await page.locator('.wizard').evaluate(element=>getComputedStyle(element).colorScheme)).toBe('light');
 await card.screenshot({path:`.runtime/readable-plan-${width}.png`});
 await details.click();await expect(page.getByRole('heading',{name:'Why this plan fits you',exact:true})).toBeVisible();
 await page.evaluate(async()=>{const headers={'Content-Type':'application/json','X-Journey-Session':sessionStorage.getItem('helm-journey') || ''};const response=await fetch('/api/journey/wizard/access',{method:'POST',headers,body:JSON.stringify({hours:24})});if(!response.ok)throw new Error('Access fixture failed');const {url}=await response.json();const exchange=await fetch('/api/journey/access-links/exchange',{method:'POST',headers,body:JSON.stringify({token:url.split('#')[1]})});if(!exchange.ok)throw new Error('Exchange fixture failed');});
 await page.goto('/my-quotes');await expect(page.getByRole('link',{name:'Download synthetic quotation PDF'})).toHaveCount(2,{timeout:25000});
 const quote=page.locator('.j-card').first();await readable(quote);await quote.getByRole('button',{name:'Ask about this quotation'}).hover();await readable(quote);
 await quote.screenshot({path:`.runtime/readable-dashboard-${width}.png`});
 const scan=await new AxeBuilder({page}).include('.w-dashboard').analyze();expect(scan.violations.filter(v=>['serious','critical'].includes(v.impact || ''))).toEqual([]);
 await page.goto('/get-cover/quote/budget');await expect(page.getByRole('heading',{name:'Your monthly budget.'})).toBeVisible();
 await expect(page.getByRole('button',{name:'No target',exact:true})).toHaveAttribute('aria-pressed','true');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 await page.getByRole('button',{name:'Ask Helm',exact:true}).click();await expect(page.locator('.hc-panel')).toBeVisible();await page.getByRole('button',{name:'Close assistant',exact:true}).click();
 await page.screenshot({path:`.runtime/light-form-${width}.png`});
 const next=page.getByRole('button',{name:'Next',exact:true});await expect(next).toBeEnabled();
 const bounds=await next.boundingBox();expect(bounds).toBeTruthy();
 expect(await next.evaluate(element=>{const r=element.getBoundingClientRect();const target=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return target===element || element.contains(target);})).toBeTruthy();
 await next.click();await expect(page.getByRole('heading',{name:'Your maximum excess.'})).toBeVisible();
});
