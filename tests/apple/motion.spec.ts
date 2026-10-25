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
