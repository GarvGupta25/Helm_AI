import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('helm-cookie-consent-v1', JSON.stringify({ necessary: true })));
});

test('English guided intake remains usable on a narrow viewport', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/get-cover/quote');
  await page.getByRole('button', { name: 'Let the AI ask me', exact: true }).click();
  await expect(page.locator('.j-interview')).toHaveAttribute('dir', 'ltr');
  const scan = await new AxeBuilder({ page }).include('.journey').analyze();
  expect(scan.violations.filter(v => ['serious', 'critical'].includes(v.impact || ''))).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
});

test('manual and guided modes share saved answers without invented defaults', async ({ page }) => {
  await page.goto('/get-cover/quote');
  await page.getByRole('button', { name: 'Add adult', exact: true }).click();
  await page.getByLabel('Person 1 age', { exact: true }).fill('35');
  await page.getByRole('button', { name: 'Let the AI ask me', exact: true }).click();
  await expect(page.getByText('35', { exact: true }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Fill it in myself', exact: true }).click();
  await expect(page.getByLabel('Person 1 age', { exact: true })).toHaveValue('35');
  await page.getByRole('button', { name: 'Save draft', exact: true }).click();
  await page.reload();
  await expect(page.getByLabel('Person 1 age', { exact: true })).toHaveValue('35');
  await page.getByRole('button', { name: 'Get recommendations', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Missing essential answers' })).toBeVisible();
  await expect(page.getByText('Confirmed version 1.', { exact: false })).toBeVisible();
});

test('confirmed intake produces a persistent selectable comparison and a nonselectable preview', async ({ page }) => {
  await page.goto('/get-cover/quote');
  await page.getByRole('button', { name: 'Add adult', exact: true }).click();
  await page.getByLabel('Person 1 age', { exact: true }).fill('35');
  await page.getByLabel('Region · mandatory', { exact: true }).selectOption('England');
  await page.getByLabel('Cover start date · mandatory', { exact: true }).fill(new Date().toISOString().slice(0, 10));
  await page.getByLabel('Monthly budget · mandatory choice', { exact: true }).selectOption('amount');
  await page.getByLabel('Budget in pounds', { exact: true }).fill('150');
  await page.getByLabel('Maximum excess · mandatory choice', { exact: true }).selectOption('50000');
  await page.getByLabel('Hospital list · mandatory choice', { exact: true }).selectOption('1');
  await page.getByRole('checkbox', { name: 'I have reviewed my essential benefits, including choosing none' }).check();
  await page.getByRole('button', { name: 'Get recommendations', exact: true }).click();
  await expect(page.locator('.j-card')).toHaveCount(3);
  await page.getByRole('button', { name: /^Ask about Research/ }).first().click();
  await page.getByRole('button', { name: 'Break down my premium', exact: true }).click();
  await expect(page.getByText('Monthly base', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: 'Close policy questions' }).click();
  await page.locator('.j-card input[type=checkbox]').first().check();
  await page.getByRole('button', { name: 'Review selected plans (1)', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Review your selected plans' })).toBeVisible();
  await page.reload();
  await expect(page.locator('.j-card input[type=checkbox]').first()).toBeChecked();
  await page.getByRole('button', { name: 'Review selected plans (1)', exact: true }).click();
  await page.getByLabel('Fictional contact', { exact: true }).fill('browser@example.test');
  await page.getByRole('checkbox', { name: /I understand that verification/ }).check();
  await page.getByRole('button', { name: 'Get demo verification code', exact: true }).click();
  const code = await page.getByText('One-time simulation code:', { exact: false }).locator('strong').innerText();
  await page.getByLabel('One-time demo code', { exact: true }).fill(code);
  await page.getByRole('button', { name: 'Verify demo contact', exact: true }).click();
  await page.getByRole('checkbox', { name: /I explicitly consent to share this reviewed fictional profile/ }).check();
  await page.getByRole('button', { name: 'Request simulated quotations', exact: true }).click();
  await expect(page.getByText('Your demo case is saved', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Preview £30 more budget' }).click();
  await expect(page.getByText('What-if preview. You cannot select these results.')).toBeVisible();
  await expect(page.locator('.j-card input[type=checkbox]')).toHaveCount(0);
  await page.getByRole('button', { name: 'Return to confirmed results' }).click();
  await expect(page.locator('.j-card input[type=checkbox]').first()).toBeChecked();
  await page.getByRole('button', { name: 'Review selected plans (1)', exact: true }).click();
  // Reloading the comparison recreates the request UI; use its saved bookmark for access.
  await page.evaluate(async () => {
    const capability = sessionStorage.getItem('helm-journey');
    const caseId = sessionStorage.getItem('helm-journey-case');
    const response = await fetch('/api/journey/access-links', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Journey-Session': capability || '' }, body: JSON.stringify({ case_id: caseId, hours: 24 }) });
    if (!response.ok) throw new Error('Private link could not be created');
  });
  const privateUrl = await page.evaluate(async () => {
    const response = await fetch('/api/journey/demo/inbox', { headers: { 'X-Journey-Session': sessionStorage.getItem('helm-journey') || '' } });
    const jobs = await response.json();
    return jobs.find((job: { kind: string }) => job.kind === 'access_link').content.url as string;
  });
  await page.goto(privateUrl);
  await page.getByRole('button', { name: 'Open private dashboard', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Your quotations, together.' })).toBeVisible();
  await expect(page).toHaveURL(/\/quote-dashboard$/);
  await expect(async () => {
    await page.getByRole('button', { name: 'Refresh quotations', exact: true }).click();
    await expect(page.getByRole('link', { name: 'Download synthetic quotation PDF' }).first()).toBeVisible();
  }).toPass({ timeout: 20000 });
  const download = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Download synthetic quotation PDF' }).first().click();
  expect((await download).suggestedFilename()).toMatch(/^helm-demo-quote-.*\.pdf$/);
  const scan = await new AxeBuilder({ page }).include('.journey').analyze();
  expect(scan.violations.filter(v => ['serious', 'critical'].includes(v.impact || ''))).toEqual([]);
});
