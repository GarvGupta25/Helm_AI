import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('helm-cookie-consent-v1', JSON.stringify({ necessary: true })));
});
const y = (page: Page) => page.locator('.apple-sheet').evaluate(el => parseFloat((el as HTMLElement).style.getPropertyValue('--sheet-y')) || 0);
async function openSheet(page: Page) {
  await page.goto('/'); await page.getByRole('button', { name: 'Read how Helm works', exact: true }).click();
  await expect(page.locator('.apple-sheet')).toHaveAttribute('data-sheet-ready','true');
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect.poll(() => y(page)).toBeCloseTo(0, 0);
}
test('press begins before release, cancels when moved away and never navigates on down', async ({ page }) => {
  await page.goto('/');
  const button = page.getByRole('button', { name: 'Read how Helm works', exact: true }); await button.scrollIntoViewIfNeeded(); const box = (await button.boundingBox())!;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2); await page.mouse.down();
  await expect(button).toHaveAttribute('data-pressed');
  await expect.poll(() => button.evaluate(el => Number(getComputedStyle(el).scale))).toBeCloseTo(.97, 2);
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.mouse.move(5, 5); await expect(button).not.toHaveAttribute('data-pressed'); await page.mouse.up();
  await expect(page.getByRole('dialog')).toHaveCount(0);
});
for (const width of [1440, 390]) test(`sheet tracks, resists, cancels and dismisses with keyboard at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1000 }); await openSheet(page);
  const bounds=await page.getByRole('dialog').boundingBox();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);expect(bounds!.x+bounds!.width).toBeLessThanOrEqual(width);
  const handle = page.locator('.apple-sheet-grab'); const rect = (await handle.boundingBox())!;
  const x = rect.x + rect.width / 2; const top = rect.y + rect.height / 2;
  await page.mouse.move(x, top); await page.mouse.down(); await page.mouse.move(x, top + 6);
  expect(Math.abs(await y(page))).toBeLessThan(1);
  await page.mouse.move(x, top + 60); expect(await y(page)).toBeCloseTo(60, 0);
  await page.mouse.move(x, top - 60); const resistance = await y(page); expect(resistance).toBeLessThan(0); expect(resistance).toBeGreaterThan(-60);
  await page.mouse.up(); await expect.poll(() => y(page)).toBeCloseTo(0, 0);
  const scan = await new AxeBuilder({ page }).include('[role=dialog]').analyze();
  expect(scan.violations.filter(v => ['serious', 'critical'].includes(v.impact || ''))).toEqual([]);
  await page.screenshot({ path: `.runtime/apple-sheet-${width}.png` });
  await page.keyboard.press('Escape'); await expect(page.getByRole('dialog')).toHaveCount(0);
});
test('closing can be caught and reversed from its presentation position', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 1000 }); await openSheet(page);
  await page.clock.install({time:new Date('2026-10-25T12:00:00Z')});
  await page.clock.pauseAt(new Date('2026-10-25T12:01:00Z'));
  await page.getByRole('button', {name:'Close dialog',exact:true}).evaluate((el:HTMLElement)=>el.click());
  await page.clock.runFor(32);
  const handle = page.locator('.apple-sheet-grab'); const rect=(await handle.boundingBox())!;
  await page.mouse.move(rect.x + rect.width / 2, rect.y + rect.height / 2); await page.mouse.down();
  const caught = await y(page);
  await page.mouse.move(rect.x + rect.width / 2, rect.y + rect.height / 2 - 60);
  expect(await y(page)).toBeLessThan(caught);
  await page.mouse.up(); await page.clock.runFor(1500); await expect.poll(() => y(page)).toBeCloseTo(0, 0);
  await expect(page.getByRole('dialog')).toBeVisible();
  const next = (await handle.boundingBox())!; const x = next.x + next.width / 2; const top = next.y + next.height / 2;
  await page.mouse.move(x, top); await page.mouse.down(); await page.mouse.move(x, top + 350, { steps: 8 }); await page.mouse.up(); await page.clock.runFor(1500);
  await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('reduced motion crossfades without travel and responds to live preference changes', async ({ page }) => {
  await page.emulateMedia({ reducedMotion:'reduce' }); await openSheet(page);
  await expect(page.locator('.apple-sheet')).toHaveAttribute('data-reduced-motion','true');
  expect(await y(page)).toBe(0);
  const rect=(await page.locator('.apple-sheet-grab').boundingBox())!;
  await page.mouse.move(rect.x+rect.width/2,rect.y+rect.height/2);await page.mouse.down();
  await page.mouse.move(rect.x+rect.width/2,rect.y+150);expect(await y(page)).toBe(0);await page.mouse.up();
  await page.emulateMedia({reducedMotion:'no-preference'});
  await expect(page.locator('.apple-sheet')).toHaveAttribute('data-reduced-motion','false');
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.getByRole('button',{name:'Close dialog',exact:true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('navbar has one glass layer, solid accessible alternatives and size-aware type',async({page})=>{
  await page.goto('/');
  await expect(page.locator('.uk-hero-copy h1')).toBeVisible();
  const header=page.locator('.uk-header');
  expect(await header.evaluate(el=>getComputedStyle(el).backdropFilter)).toBe('blur(20px) saturate(1.8)');
  expect(await header.locator('*').evaluateAll(nodes=>nodes.filter(el=>getComputedStyle(el).backdropFilter!=='none').length)).toBe(0);
  const typography=await page.evaluate(()=>{
    const heading=getComputedStyle(document.querySelector('h1')!);const body=getComputedStyle(document.querySelector('.uk-hero-copy p')!);
    return {tracking:parseFloat(heading.letterSpacing)/parseFloat(heading.fontSize),leading:parseFloat(heading.lineHeight)/parseFloat(heading.fontSize),bodyTracking:body.letterSpacing};
  });
  expect(typography.tracking).toBeCloseTo(-.02,3);expect(typography.leading).toBeCloseTo(1.05,2);
  const cdp=await page.context().newCDPSession(page);
  await cdp.send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-transparency',value:'reduce'},{name:'prefers-contrast',value:'more'}]});
  await expect.poll(()=>header.evaluate(el=>getComputedStyle(el).backdropFilter)).toBe('none');
  await expect.poll(()=>header.evaluate(el=>getComputedStyle(el).backgroundColor)).toBe('rgb(5, 59, 68)');
  await openSheet(page);
  await expect(page.locator('.apple-sheet')).toHaveAttribute('data-reduced-transparency','true');
  await expect(page.locator('.apple-sheet')).toHaveAttribute('data-more-contrast','true');
  await page.screenshot({path:'.runtime/apple-contrast-sheet.png'});
});

test('dev routes and dialogs load without browser console errors',async({page})=>{
  const errors:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('console',message=>{if(message.type()==='error')errors.push(message.text()+' '+message.location().url);});
  for(const route of ['/','/about','/get-cover/quote']){
    await page.goto(route);await expect(page.getByRole('heading',{level:1})).toBeVisible();
  }
  await page.goto('/');await page.getByRole('button',{name:'Search website',exact:true}).click();
  await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect(errors).toEqual([]);
});
