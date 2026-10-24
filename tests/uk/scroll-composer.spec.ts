import { test, expect } from '@playwright/test';

for (const width of [375, 1280]) {
  test(`scrolling keeps page geometry stable at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.emulateMedia({ reducedMotion: 'no-preference' });
    await page.addInitScript(() => localStorage.setItem('helm-cookie-consent-v1', JSON.stringify({ necessary: true })));
    for (const route of ['/', '/about', '/contact']) {
      await page.goto(route);
      await expect(page.locator('h1')).toBeVisible();
      await page.evaluate(() => document.fonts.ready);
      const mainTop = await page.locator('#uk-main').evaluate(el => el.getBoundingClientRect().top + window.scrollY);
      await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'instant' }));
      await expect(page.locator('.uk-header')).toHaveClass(/pill/);
      expect(await page.locator('#uk-main').evaluate(el => el.getBoundingClientRect().top + window.scrollY)).toBeCloseTo(mainTop, 0);
      await expect(page.locator('.uk-header')).toHaveClass(/hidden/);
      // Small momentum deltas must not flash the header back into view.
      await page.evaluate(() => window.scrollBy({ top: 2, behavior: 'instant' }));
      await expect(page.locator('.uk-header')).toHaveClass(/hidden/);
      await page.evaluate(() => window.scrollBy({ top: -60, behavior: 'instant' }));
      await expect(page.locator('.uk-header')).not.toHaveClass(/hidden/);
    }
  });
}

test('chat composer keeps aligned controls, one focus ring and multiline keyboard input', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  const reject = page.getByRole('button', { name: 'Reject all', exact: true });
  if (await reject.isVisible()) await reject.click();
  await page.getByRole('button', { name: 'Open the Helm AI assistant' }).click();
  const input = page.getByRole('textbox', { name: 'Type your message' });
  await expect(input).toBeFocused();
  const styles = await input.evaluate(el => ({ border: getComputedStyle(el).borderTopWidth, outline: getComputedStyle(el).outlineStyle }));
  expect(styles).toEqual({ border: '0px', outline: 'none' });
  await input.fill('Explain excess');
  await input.press('Shift+Enter');
  await input.press('a');
  await expect(input).toHaveValue('Explain excess\na');
  const buttons = await page.locator('.hc-composer > button').evaluateAll(elements => elements.map(el => ({ width: el.getBoundingClientRect().width, height: el.getBoundingClientRect().height })));
  expect(buttons).toHaveLength(2);
  for (const button of buttons) expect(button).toEqual({ width: 44, height: 44 });
  await input.press('Enter');
  await expect(page.getByText(/An excess is the amount/)).toBeVisible();
});
