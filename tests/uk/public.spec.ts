import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { mkdirSync, writeFileSync } from 'node:fs';

const evidence = 'docs/uk/evidence';
test.beforeAll(() => mkdirSync(evidence, { recursive: true }));
async function consent(page: import('@playwright/test').Page) {
  await expect(page.locator('.uk-header')).toBeVisible({ timeout: 30_000 });
  const hasChoice = await page.evaluate(() => !!localStorage.getItem('helm-cookie-consent-v1'));
  if (!hasChoice) await page.getByRole('button', { name: 'Reject all', exact: true }).click();
}

for (const width of [375, 768, 1280, 1920]) {
  test(`home and About fit ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    for (const route of ['/', '/about']) {
      await page.goto(route); await consent(page);
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
      await page.evaluate(() => document.fonts.ready);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
      await page.screenshot({ path: `${evidence}/${route === '/' ? 'home' : 'about'}-${width}.png` });
    }
  });
}

test('WCAG automated checks on public routes', async ({ page }) => {
  test.setTimeout(300_000);
  await page.setViewportSize({ width: 1280, height: 900 });
  for (const route of ['/', '/about', '/get-cover/underwriting', '/get-cover/quote', '/legal/privacy']) {
    await page.goto(route); await consent(page);
    const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
    writeFileSync(`${evidence}/axe-${route.replaceAll('/', '-') || 'home'}.json`, JSON.stringify(result.violations, null, 2));
    expect(result.violations.filter(item => ['critical', 'serious'].includes(item.impact || '')), JSON.stringify(result.violations, null, 2)).toEqual([]);
  }
});

test('keyboard navigation, search, cookies and external-link guard', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 }); await page.goto('/'); await consent(page);
  const trigger = page.locator('.uk-desktop-nav').getByRole('button', { name: 'Get Cover', exact: true });
  await trigger.focus(); await page.keyboard.press('Enter'); await expect(trigger).toHaveAttribute('aria-expanded', 'true');
  await page.keyboard.press('Escape'); await expect(trigger).toHaveAttribute('aria-expanded', 'false');
  await page.keyboard.press('Control+k'); await expect(page.getByRole('dialog', { name: 'What can we help you find?' })).toBeVisible();
  await page.getByPlaceholder('Try underwriting or claims').fill('underwriting');
  await page.getByRole('link', { name: 'Underwriting explained', exact: true }).click();
  await expect(page).toHaveURL(/underwriting/);
  await page.getByRole('button', { name: 'Cookie settings', exact: true }).click();
  await page.getByRole('button', { name: 'Reject all', exact: true }).click();
  const stored = await page.evaluate(() => JSON.parse(localStorage.getItem('helm-cookie-consent-v1') || '{}'));
  expect(stored.analytics).toBe(false); expect(stored.marketing).toBe(false);
  await page.getByRole('link', { name: /Check a real firm/ }).click();
  await expect(page.getByRole('dialog', { name: 'You’re leaving Helm' })).toBeVisible();
  await page.getByRole('button', { name: 'Go back', exact: true }).click();
});

test('mobile navigation traps focus and reduced motion stops loops', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 }); await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/'); await consent(page); await page.getByRole('button', { name: 'Open navigation' }).click();
  const dialog = page.getByRole('dialog', { name: 'Explore Helm' }); await expect(dialog).toBeVisible();
  await page.keyboard.press('Tab'); expect(await dialog.evaluate(el => el.contains(document.activeElement))).toBeTruthy();
  await page.keyboard.press('Escape'); await expect(dialog).not.toBeVisible();
  expect(await page.locator('.uk-video-badge>svg').evaluate(el => getComputedStyle(el).animationName)).toBe('none');
});

test('576-plan quotation through review and persistent zero-payment confirmation', async ({ page }) => {
  await page.goto('/get-cover/legacy-demo'); await consent(page);
  await expect(page.getByRole('heading', { name: 'Find cover that fits your needs.' })).toBeVisible();
  let oldCalls = 0;
  page.on('request', req => { if (new URL(req.url()).pathname === '/api/uk/quotes') oldCalls++; });
  await page.getByRole('button', { name: 'Get my recommendations' }).click();
  await expect(page.locator('.research-cards article')).toHaveCount(3);
  await expect(page.getByRole('heading', { name: 'Your computed shortlist' })).toBeVisible();
  await page.locator('.research-cards article').first().getByText('Why this result?', { exact: true }).click();
  await expect(page.getByText('Standard score contributions').first()).toBeVisible();
  await page.getByRole('button', { name: 'Select this plan', exact: true }).first().click();
  const review = page.getByRole('region', { name: 'Review selected plan' });
  await expect(review).toBeVisible();
  const confirm = review.getByRole('button', { name: 'Confirm demo selection (£0 collected)' });
  await expect(confirm).toBeDisabled();
  await review.getByRole('button', { name: 'Read selected plan key facts' }).click();
  await expect(page.getByRole('heading', { name: 'Synthetic clause evidence' })).toBeVisible();
  for (const checkbox of await review.getByRole('checkbox').all()) await checkbox.check();
  await page.screenshot({ path: 'docs/chatbot-screenshots/quote-review.png' });
  await confirm.click();
  await expect(page.getByRole('heading', { name: 'Demo confirmation' })).toBeVisible();
  await expect(page.getByText('No money collected. No insurance contract created.')).toBeVisible();
  await page.screenshot({ path: 'docs/chatbot-screenshots/quote-confirmation.png' });
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download confirmation & key facts' }).click();
  expect((await download).suggestedFilename()).toBe('helm-demo-quote-confirmation.json');
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Demo confirmation' })).toBeVisible();
  expect(oldCalls).toBe(0);
  await page.goto('/research');
  await expect(page).toHaveURL(/get-cover\/quote$/);
});

test('public chat safety and support reference', async ({ page }) => {
  await page.goto('/'); await consent(page); await page.getByRole('button', { name: 'Open the Helm AI assistant' }).click();
  const input = page.getByRole('textbox', { name: 'Type your message' }); await input.fill('I have chest pain'); await page.getByRole('button', { name: /^Send(?: message)?$/, exact: true }).click();
  await expect(page.getByText(/If this is a medical emergency/)).toBeVisible();
  await input.fill('I want to complain'); await page.getByRole('button', { name: /^Send(?: message)?$/, exact: true }).click();
  await expect(page.getByText(/Demo support reference:/)).toBeVisible();
});
