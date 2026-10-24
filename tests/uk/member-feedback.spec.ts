import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('helm-cookie-consent-v1', JSON.stringify({ necessary: true })));
});

test('a newly registered member is saved and can sign back in without policies', async ({ page }) => {
  const email = `browser-${Date.now()}@example.test`;
  const password = 'Browser-only demo password';
  await page.goto('/signup');
  await expect(page.getByRole('heading', { name: 'Make yourself at home.' })).toBeVisible();
  const scan = await new AxeBuilder({ page }).include('.m-auth').analyze();
  expect(scan.violations.filter(v => ['serious', 'critical'].includes(v.impact || ''))).toEqual([]);
  await page.getByLabel('Full name', { exact: true }).fill('Browser Visitor');
  await page.getByLabel('Email address', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Create account', exact: true }).click();
  await expect(page).toHaveURL(/\/member$/);
  await expect(page.getByText('Welcome, Browser.', { exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'A fresh start. A little more clarity.' })).toBeVisible();
  await page.reload();
  await expect(page.getByText('Welcome, Browser.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await page.getByLabel('Email address', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByText('Welcome, Browser.', { exact: true })).toBeVisible();
  await expect(page.locator('.m-policy')).toHaveCount(0);
});

test('the two saved demo accounts have distinct responsive landing pages', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/login');
  await page.getByRole('button', { name: 'New member No policies yet', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'A fresh start. A little more clarity.' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Find my cover', exact: true })).toBeVisible();
  await page.screenshot({ path: '.runtime/member-new-desktop.png', fullPage: true });
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await page.getByRole('button', { name: 'Policyholder A fictional policy, ready to explore', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Your cover. A clearer view.' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Helm Balanced', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'View policy details' }).click();
  await expect(page.getByRole('region', { name: 'Policy details' })).toContainText('£250.00');
  await page.screenshot({ path: '.runtime/member-policyholder-desktop.png', fullPage: true });
  for (const width of [1440, 375]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    const scan = await new AxeBuilder({ page }).include('.m-home').analyze();
    expect(scan.violations.filter(v => ['serious', 'critical'].includes(v.impact || ''))).toEqual([]);
  }
  await page.screenshot({ path: '.runtime/member-policyholder-mobile.png', fullPage: true });
});

test('upload choices are clear, consented and English only on mobile', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.emulateMedia({ colorScheme: 'dark' });
  await page.goto('/');
  await page.getByRole('button', { name: 'Open the Helm AI assistant' }).click();
  await page.getByRole('button', { name: 'Attach a file', exact: true }).click();
  const panel = page.getByRole('region', { name: 'Add a sample document' });
  await expect(panel.getByRole('button', { name: /Upload PDF/ })).toBeDisabled();
  await panel.getByLabel('I agree to temporary file processing').check();
  await expect(panel.getByRole('button', { name: /Upload PDF/ })).toBeEnabled();
  await expect(panel.getByRole('button', { name: /Upload photo/ })).toBeEnabled();
  await expect(panel.getByRole('button', { name: /Take photo/ })).toBeEnabled();
  const scan = await new AxeBuilder({ page }).include('.hc-panel').analyze();
  expect(scan.violations.filter(v => ['serious', 'critical'].includes(v.impact || ''))).toEqual([]);
  await page.screenshot({ path: '.runtime/chat-upload-modern-mobile.png' });
  await page.getByRole('button', { name: 'Close upload options' }).click();
  await page.getByRole('button', { name: 'Conversation options' }).click();
  await expect(page.getByRole('button', { name: /العربية/ })).toHaveCount(0);
});

test('each response has saved feedback, issue reporting and controllable read aloud', async ({ page }) => {
  await page.addInitScript(() => {
    class Speech { text: string; lang = ''; onend = null; onerror = null; constructor(text: string) { this.text = text; } }
    Object.defineProperty(window, 'SpeechSynthesisUtterance', { value: Speech, configurable: true });
    Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: { getVoices: () => [], speak: () => {}, cancel: () => {} } });
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Open the Helm AI assistant' }).click();
  await page.getByRole('textbox', { name: 'Type your message' }).fill('What is an excess?');
  await page.getByRole('button', { name: 'Send message', exact: true }).click();
  const response = page.locator('.hc-message--assistant').last();
  await expect(response.getByRole('button', { name: 'Helpful', exact: true })).toBeVisible();
  await response.getByRole('button', { name: 'Read message aloud', exact: true }).click();
  await expect(response.getByRole('button', { name: 'Stop reading', exact: true })).toBeVisible();
  await response.getByRole('button', { name: 'Stop reading', exact: true }).click();
  const saved = page.waitForResponse(r => r.url().endsWith('/api/public/assistant/feedback') && r.request().method() === 'POST');
  await response.getByRole('button', { name: 'Helpful', exact: true }).click();
  expect((await (await saved).json()).recorded).toBe(true);
  await response.getByRole('button', { name: 'Not helpful', exact: true }).click();
  const form = page.getByRole('form', { name: 'Response feedback' });
  await expect(form).toBeVisible();
  await form.getByLabel('Feedback details', { exact: true }).fill('Please explain the example more clearly.');
  await form.getByRole('button', { name: 'Send feedback', exact: true }).click();
  await expect(page.getByRole('status').filter({ hasText: 'feedback saved' })).toBeVisible();
  await response.getByRole('button', { name: 'Report an issue with this answer', exact: true }).click();
  const report = page.getByRole('form', { name: 'Report a chat issue' });
  await report.getByLabel('Feedback category', { exact: true }).selectOption('technical');
  await report.getByLabel('Feedback details', { exact: true }).fill('The audio button needs a clearer label.');
  await expect(report.getByRole('checkbox')).not.toBeChecked();
  await report.getByRole('button', { name: 'Send feedback', exact: true }).click();
  await expect(page.getByRole('status').filter({ hasText: 'issue report saved' })).toBeVisible();
  await page.screenshot({ path: '.runtime/chat-response-actions.png' });
});
