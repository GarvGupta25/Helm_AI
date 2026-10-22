import { test, expect, type Page } from './support';

const config = { auth_configured: false, supabase_url: '', supabase_anon_key: '', ai_available: false, voice_available: false, payment_provider: 'simulator' };
const providerName = 'Emirates International Health and Family Assurance — نور الهدى';
const plans = Array.from({ length: 50 }, (_, index) => ({
  id: `scheme-${index}`, provider_id: index < 5 ? 'partner-one' : 'partner-two', provider_name: providerName,
  name: index === 0 ? 'WorldwideHealthCoverForSelfSponsoredResidentsAndTheirFamilies — 王秀英' : `Family care ${index + 1}`,
  annual_premium: index === 0 ? 12345678.90 : 8500 + index,
  annual_limit: 99999999.99, network: index === 0 ? 'wide' : 'standard', deductible: 500,
  outpatient_copay_pct: 20, maternity: { covered: false }, chronic_preexisting: { covered: false }, dental_optical: 'none',
}));

async function catalogue(page: Page, items = plans) {
  await page.route('**/api/config', route => route.fulfill({ json: config }));
  await page.route('**/api/public/marketplace-plans', route => route.fulfill({ json: { plans: items } }));
  await page.route('**/api/public/marketplace-partners', route => route.fulfill({ json: { items: [{ id: 'partner-one', provider_id: 'partner-one', name: providerName, tier: 'marketplace_partner', emirate: 'UAE demonstration', scheme_count: 5 }] } }));
}

for (const width of [320, 768, 1440]) {
  test(`public catalogue wraps realistic worst-case data at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    await catalogue(page);
    for (const path of ['/', '/plans', '/partners']) {
      await page.goto(path);
      await expect(page.locator('h1')).toBeVisible();
      if (path === '/plans') await expect(page.getByRole('status')).toContainText('50 schemes found');
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);
      await page.screenshot({ path: info.outputPath(`${path.replaceAll('/', '') || 'home'}-${width}.png`) });
    }
    await page.goto('/plans');
    await page.getByLabel('Search schemes').fill('not-an-existing-scheme');
    await expect(page.getByRole('heading', { name: 'No schemes found' })).toBeVisible();
    await page.getByRole('button', { name: 'Show all schemes' }).click();
    await expect(page.locator('.scheme-card')).toHaveCount(50);
    await page.getByRole('combobox', { name: 'Network', exact: true }).selectOption('wide');
    await expect(page.getByRole('status')).toHaveText('1 scheme found.');
  });
}

test('partner links filter its schemes and empty catalogue has a recovery action', async ({ page }) => {
  await catalogue(page);
  await page.goto('/partners');
  await page.getByRole('link', { name: new RegExp(providerName) }).click();
  await expect(page).toHaveURL(/provider=partner-one/);
  await expect(page.getByRole('status')).toHaveText('5 schemes found for this partner.');
  await page.route('**/api/public/marketplace-plans', route => route.fulfill({ json: { plans: [] } }));
  await page.reload();
  await expect(page.getByRole('heading', { name: 'No schemes found' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Show all schemes' })).toBeEnabled();
});

test('assistant supports keyboard editing, rate-limit recovery, focus return and dismissal', async ({ page }) => {
  await catalogue(page, []);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.clock.install();
  await page.goto('/');
  await expect(page.locator('h1')).toBeVisible();
  await page.clock.fastForward(60000);
  await page.getByRole('button', { name: 'Dismiss message' }).click();
  await page.reload();
  await expect(page.getByRole('button', { name: 'Dismiss message' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Open the Helm AI assistant' }).click();
  await expect(page.getByRole('button', { name: 'Close assistant' })).toBeFocused();
  await page.route('**/api/public/assistant/messages', route => route.fulfill({ status: 429, json: {} }));
  const input = page.getByRole('textbox', { name: 'Type your message' });
  await input.fill('What does my policy include?');
  await input.press('Shift+Enter');
  await expect(input).toHaveValue('What does my policy include?\n');
  await input.press('Enter');
  await expect(page.getByRole('alert')).toContainText('message limit');
  await expect(input).toBeEnabled();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Open the Helm AI assistant' })).toBeFocused();
});

test('mobile navigation closes with Escape and long text remains reachable at 200% text size', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  await catalogue(page, plans.slice(0, 1));
  await page.goto('/plans');
  await page.getByRole('button', { name: 'Open navigation' }).click();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: 'Open navigation' })).toBeFocused();
  await page.addStyleTag({ content: 'html { font-size: 200%; }' });
  await expect(page.locator('.scheme-card')).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);
});
