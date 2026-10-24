import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
const evidence = 'docs/chatbot-screenshots';
test.beforeAll(() => mkdirSync(evidence, { recursive: true }));
test.beforeEach(async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.addInitScript(() => { localStorage.setItem('helm-cookie-consent-v1', JSON.stringify({ necessary: true, analytics: false, marketing: false })); });
});

test('research confirmed reranking, what-if, undo, consent and delete', async ({ page }) => {
  await page.goto('/get-cover/legacy-demo');
  await page.getByRole('button', { name: 'Get my recommendations' }).click();
  await expect(page.getByRole('heading', { name: 'Your computed shortlist' })).toBeVisible();
  await expect(page.locator('.research-cards article')).toHaveCount(3);
  await page.getByLabel('Describe a preference change').fill('Mental health is essential, excess below £250');
  await page.getByRole('button', { name: 'Review proposed changes' }).click();
  await expect(page.getByText('Confirm these changes before reranking.')).toBeVisible();
  await page.getByRole('button', { name: 'Confirm these changes', exact: true }).click();
  await expect(page.getByText(/Profile version 2/)).toBeVisible();
  await page.getByRole('button', { name: 'Select this plan', exact: true }).first().click();
  await page.getByRole('button', { name: 'What if my budget rose by £30?' }).click();
  await expect(page.getByRole('region', { name: 'Review selected plan' })).not.toBeVisible();
  await expect(page.locator('.research-cards').getByRole('button', { name: 'Select this plan' })).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'What-if preview' })).toBeVisible();
  await page.getByRole('button', { name: 'Return to confirmed results' }).click();
  await page.getByRole('button', { name: 'Undo last confirmed change' }).click();
  await expect(page.getByText(/Profile version 3/)).toBeVisible();
  await page.getByLabel('Remember confirmed soft preferences for 90 days').check();
  await expect(page.getByText(/Confirmed soft benefit preferences saved/)).toBeVisible();
  await page.screenshot({ path: `${evidence}/research-desktop.png`, fullPage: true });
  const scan = await new AxeBuilder({ page }).include('.research').analyze();
  writeFileSync(`${evidence}/research-axe.json`, JSON.stringify(scan.violations, null, 2));
  expect(scan.violations.filter(v => ['serious', 'critical'].includes(v.impact || ''))).toEqual([]);
  await page.getByRole('button', { name: 'Delete session & memory' }).click();
  await expect(page.getByText('Session and memory deleted.')).toBeVisible();
});

test('chat empty, conversation, refresh, clear undo and transcript', async ({ page }) => {
  await page.goto('/');
  await page.screenshot({ path: `${evidence}/desktop-closed.png` });
  await page.getByRole('button', { name: 'Open the Helm AI assistant' }).click();
  await expect(page.locator('.hc-panel')).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Type your message' })).toBeFocused();
  await page.screenshot({ path: `${evidence}/desktop-empty.png` });
  const input = page.getByRole('textbox', { name: 'Type your message' });
  await input.fill("What's an excess?"); await page.getByRole('button', { name: 'Send message', exact: true }).click();
  await expect(page.getByText(/An excess is the amount/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Stop response' })).not.toBeVisible();
  await page.screenshot({ path: `${evidence}/desktop-conversation.png` });
  const scan = await new AxeBuilder({ page }).include('.hc-panel').analyze();
  writeFileSync(`${evidence}/chat-axe.json`, JSON.stringify(scan.violations, null, 2));
  expect(scan.violations.filter(v => ['serious', 'critical'].includes(v.impact || ''))).toEqual([]);
  await page.reload(); await expect(page.getByText(/An excess is the amount/)).toBeVisible();
  await page.getByRole('button', { name: 'Conversation options' }).click();
  const download = page.waitForEvent('download'); await page.getByRole('button', { name: 'Download transcript' }).click();
  expect((await download).suggestedFilename()).toBe('helm-conversation.txt');
  await page.getByRole('button', { name: 'Conversation options' }).click();
  await page.getByRole('button', { name: 'New conversation', exact: true }).click();
  await page.getByRole('button', { name: 'New conversation', exact: true }).click();
  await expect(page.getByText('Conversation cleared.')).toBeVisible();
  await page.getByRole('button', { name: 'Undo', exact: true }).click();
  await expect(page.getByText(/An excess is the amount/)).toBeVisible();
  await page.keyboard.press('Escape'); await expect(page.locator('.hc-panel')).not.toBeVisible();
  await expect(page.getByRole('button', { name: 'Open the Helm AI assistant' })).toBeFocused();
});

test('mobile English dark reduced-motion layout', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 }); await page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' });
  await page.goto('/'); await page.getByRole('button', { name: 'Open the Helm AI assistant' }).click();
  await expect(page.locator('.hc-panel')).toHaveAttribute('dir', 'ltr');
  expect(await page.locator('.hc-panel').evaluate(el => el.scrollWidth <= el.clientWidth)).toBeTruthy();
  await page.screenshot({ path: `${evidence}/mobile-english-dark.png` });
  const scan = await new AxeBuilder({ page }).include('.hc-panel').analyze();
  writeFileSync(`${evidence}/chat-dark-english-axe.json`, JSON.stringify(scan.violations, null, 2));
  expect(scan.violations.filter(v => ['serious', 'critical'].includes(v.impact || ''))).toEqual([]);
});

test('voice feature detection and recording controls with simulated browser API', async ({ page }) => {
  await page.addInitScript(() => {
    class FakeRecognition { lang = ''; interimResults = false; continuous = false; onresult: unknown; onerror: unknown; onend: (() => void) | null = null; start() {} stop() { this.onend?.(); } abort() { this.onend?.(); } }
    Object.defineProperty(window, 'SpeechRecognition', { value: FakeRecognition });
  });
  await page.goto('/'); await page.getByRole('button', { name: 'Open the Helm AI assistant' }).click();
  await page.getByRole('button', { name: 'Dictate a message' }).click();
  await page.getByRole('button', { name: 'Done', exact: true }).click();
  await expect(page.getByRole('timer')).toBeVisible();
  await page.screenshot({ path: `${evidence}/desktop-recording-simulated.png` });
  await page.getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(page.getByRole('timer')).not.toBeVisible();
});

test('sample PDF upload and attachment message', async ({ page }) => {
  await page.goto('/'); await page.getByRole('button', { name: 'Open the Helm AI assistant' }).click();
  await page.getByRole('button', { name: 'Attach a file' }).click();
  await page.getByLabel('I agree to temporary file processing').check();
  const content = 'BT /F1 12 Tf 20 100 Td (Synthetic excess is a member contribution.) Tj ET';
  const pdf = `%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 200]/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n5 0 obj<</Length ${content.length}>>stream\n${content}\nendstream\nendobj\ntrailer<</Root 1 0 R>>\n%%EOF`;
  await page.locator('.hc-panel input[type=file]').setInputFiles({ name: 'sample-policy.pdf', mimeType: 'application/pdf', buffer: Buffer.from(pdf) });
  await expect(page.locator('.hc-attachment')).toContainText('sample-policy.pdf');
  await expect(page.getByRole('progressbar')).not.toBeVisible();
  await page.getByRole('button', { name: 'Attach a file' }).click();
  await page.screenshot({ path: `${evidence}/desktop-upload.png` });
  await page.getByRole('textbox', { name: 'Type your message' }).fill('Explain excess');
  await page.getByRole('button', { name: 'Send message', exact: true }).click();
  await expect(page.getByText(/I read the attachment as untrusted text/)).toBeVisible();
});

test('stop, offline recovery and non-stream fallback', async ({ page, context }) => {
  await page.goto('/'); await page.getByRole('button', { name: 'Open the Helm AI assistant' }).click();
  const input = page.getByRole('textbox', { name: 'Type your message' });
  await input.fill('Explain underwriting'); await page.getByRole('button', { name: 'Send message', exact: true }).click();
  await page.getByRole('button', { name: 'Stop response' }).click();
  await expect(page.getByText('Stopped', { exact: true })).toBeVisible();
  await context.setOffline(true); await expect(page.getByText(/You’re offline/)).toBeVisible();
  await input.fill('What is an excess?'); await expect(page.getByRole('button', { name: 'Send message', exact: true })).toBeDisabled();
  await context.setOffline(false);
  await page.route('**/api/public/assistant/stream', route => route.fulfill({ status: 404, body: '{}' }));
  await page.getByRole('button', { name: 'Send message', exact: true }).click();
  await expect(page.getByText(/An excess is the amount/)).toBeVisible();
});
