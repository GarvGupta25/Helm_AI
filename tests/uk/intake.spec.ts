import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('helm-cookie-consent-v1', JSON.stringify({ necessary: true })));
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
