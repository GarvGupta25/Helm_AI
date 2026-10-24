import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('separate broker entry stays closed without configured authentication', async ({ page }) => {
  await page.route('**/api/config', route => route.fulfill({ json: { auth_configured: false } }));
  await page.goto('/broker.html');
  await expect(page.getByRole('heading', { name: 'A clear view. A considered decision.' })).toBeVisible();
  await expect(page.getByText('Broker sign-in needs configuration.', { exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Your case queue' })).toHaveCount(0);
  for (const width of [1440, 375]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    const scan = await new AxeBuilder({ page }).analyze();
    expect(scan.violations.filter(v => ['serious', 'critical'].includes(v.impact || ''))).toEqual([]);
  }
});
