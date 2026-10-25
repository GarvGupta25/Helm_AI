import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { seedIntake } from './helpers';

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('helm-cookie-consent-v1', JSON.stringify({ necessary: true })));
});

async function selectOne(page: Page) {
  await page.goto('/get-cover/plans');
  await page.getByRole('button', { name: 'Select plan', exact: true }).first().click();
  await expect(page.getByRole('heading', { name: 'Review your choice', exact: true })).toBeVisible();
}

for (const width of [360, 768, 1024, 1440]) test(`calm checkpoint and consent review at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1000 });
  await page.emulateMedia({ reducedMotion: 'reduce', colorScheme: width === 360 ? 'dark' : 'light' });
  await seedIntake(page); await page.goto('/get-cover/quote/ready');
  await expect(page.getByRole('heading', { name: 'Your essentials are done', exact: true })).toBeVisible();
  await expect(page.getByRole('progressbar')).toHaveAttribute('value', '7');
  await expect(page.getByRole('button', { name: 'See my plans', exact: true })).toBeInViewport();
  await expect(page.getByRole('link', { name: 'Add optional details (about 2 min)', exact: true })).toHaveAttribute('href', '/get-cover/quote/optional/existing-cover');
  await expect(page.locator('h1')).toHaveCount(1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect(page.locator('.uk-desktop-nav,.uk-footer-top,.uk-footer-columns')).toHaveCount(0);
  await page.screenshot({ path: `.runtime/checkout-ready-${width}.png`, fullPage: true });
  const checkpoint = await new AxeBuilder({ page }).include('#uk-main').analyze();
  expect(checkpoint.violations.filter(v => ['serious', 'critical'].includes(v.impact || ''))).toEqual([]);
  await page.getByRole('button', { name: 'See my plans', exact: true }).click();
  await expect(page).toHaveURL(/\/get-cover\/plans$/);
  await selectOne(page);
  await expect(page.locator('h1')).toHaveCount(1);
  await expect(page.locator('.flow-premium')).toHaveText(/£\d+\.\d{2}\s*\/month/);
  await expect(page.getByText('1 of 3 plans chosen', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Request my quote', exact: true })).toBeDisabled();
  await expect(page.getByText('Tick the first box to continue.', { exact: true })).toBeVisible();
  await page.getByText('What does this mean?', { exact: true }).click();
  await expect(page.getByText(/Display filters only narrow eligible options/)).toBeVisible();
  await page.getByText('Exact profile fields shared with selected insurers', { exact: true }).click();
  await expect(page.locator('.flow-shared-fields pre')).toContainText('age_years');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const scan = await new AxeBuilder({ page }).include('#uk-main').analyze();
  expect(scan.violations.filter(v => ['serious', 'critical'].includes(v.impact || ''))).toEqual([]);
  await page.getByText('Exact profile fields shared with selected insurers', { exact: true }).click();
  await page.getByText('What does this mean?', { exact: true }).click();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: `.runtime/checkout-review-${width}.png`, fullPage: true });
  await page.getByRole('checkbox', { name: /I explicitly consent to share this reviewed fictional profile/ }).check();
  await expect(page.getByRole('button', { name: 'Request my quote', exact: true })).toBeEnabled();
});

for (const width of [1440, 360]) test(`required consent guards submission and failures recover at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1000 });
  await seedIntake(page); await selectOne(page);
  let posts = 0;
  await page.route('**/api/journey/consents', async route => { posts++; await route.continue(); });
  const cta = page.getByRole('button', { name: 'Request my quote', exact: true });
  await cta.focus(); await cta.press('Enter');
  await expect(page.getByText('Tick the first box to continue. Sharing with the broker is optional.')).toBeVisible();
  await expect(page.getByRole('checkbox', { name: /I explicitly consent/ })).toBeFocused();
  if (width < 768) {
    const checkbox = await page.getByRole('checkbox', { name: /I explicitly consent/ }).boundingBox();
    const bar = await page.locator('.flow-action').boundingBox();
    expect(checkbox!.y + checkbox!.height).toBeLessThan(bar!.y);
  }
  expect(posts).toBe(0);
  const broker = page.getByRole('checkbox', { name: /Also share my case/ });
  await broker.check(); await expect(cta).toBeDisabled(); await broker.uncheck();
  await page.getByRole('checkbox', { name: /I explicitly consent/ }).check();
  let release: () => void = () => {};
  const wait = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/journey/selection', async route => {
    if (route.request().method() !== 'POST') return route.continue();
    expect(route.request().postDataJSON().broker_consent_id).toBeNull();
    await wait; return route.fulfill({ status: 503, json: { detail: 'Please retry your selection.' } });
  });
  await cta.click();
  await expect(page.getByRole('button', { name: 'Requesting…', exact: true })).toBeDisabled();
  await page.screenshot({ path: `.runtime/checkout-loading-${width}.png`, fullPage: true });
  release(); await expect(page.getByRole('alert')).toContainText('Please retry your selection.');
  await expect(cta).toBeEnabled();
  await page.unroute('**/api/journey/selection');
  await cta.click(); await expect(page).toHaveURL(/\/get-cover\/verify$/);
});

test('slim header saves the session, opens help, and preserves edit destinations', async ({ page }) => {
  await seedIntake(page); await page.goto('/get-cover/quote/ready');
  await expect(page.getByRole('link', { name: 'Edit excess', exact: true })).toHaveAttribute('href', '/get-cover/quote/excess?return=review');
  await page.getByRole('button', { name: 'Ask Helm for help', exact: true }).click();
  await expect(page.getByRole('dialog').filter({ hasText: /Helm/ }).first()).toBeVisible();
  await page.keyboard.press('Escape');
  const token = await page.evaluate(() => sessionStorage.getItem('helm-journey'));
  await page.getByRole('button', { name: 'Save and exit', exact: true }).click();
  await expect(page).toHaveURL(/\/$/);
  expect(await page.evaluate(() => sessionStorage.getItem('helm-journey'))).toBe(token);
  await expect(page.locator('.uk-desktop-nav')).toBeVisible();
  await page.goto('/get-cover/quote/ready');
  await expect(page.getByRole('heading', { name: 'Your essentials are done', exact: true })).toBeVisible();
});
