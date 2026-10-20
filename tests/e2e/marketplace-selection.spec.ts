import { expect, test, type Page } from './support';

async function stubMemberMarketplace(page: Page) {
  let selected = false;
  await page.route('**/auth/v1/**', route => route.fulfill({ json: {
    access_token: 'member-token', refresh_token: 'member-refresh', expires_in: 3600,
    token_type: 'bearer', user: { id: 'member-1', email: 'member@example', app_metadata: {} },
  } }));
  await page.route('**/api/config', route => route.fulfill({ json: { auth_configured: true, supabase_url: 'http://127.0.0.1:54321', supabase_anon_key: 'local-demo-key', ai_available: false, voice_available: false, payment_provider: 'simulator' } }));
  await page.route('**/api/me/access', route => route.fulfill({ json: { role: 'member' } }));
  await page.route('**/api/marketplace/cases/case-1/quotations', route => route.fulfill({ json: {
    case_id: 'case-1', status: selected ? 'customer_selected' : 'quotes_collected', collection_ready: true, responded: 2, invited: 2, collection_window_hours: 72,
    quotations: [
      { rank: 1, quotation_id: 'quote-real-1', application_id: 'app-1', provider_name: 'Al Noor Takaful', premium_aed: 8200, score: 98, status: selected ? 'selected' : 'submitted', explanation: 'Strong price and network fit from the submitted terms.', terms: { name: 'Al Noor Standard', network: 'standard', annual_limit: 500000, deductible: 500, outpatient_copay_pct: 20, maternity: { covered: true, waiting_period_months: 6 } } },
      ...(!selected ? [{ rank: 2, quotation_id: 'quote-real-2', application_id: 'app-2', provider_name: 'Gulf Shield Insurance', premium_aed: 10500, score: 91, status: 'submitted', explanation: 'Wide access with a higher submitted premium.', terms: { name: 'Gulf Wide', network: 'wide', annual_limit: 800000, deductible: 250, outpatient_copay_pct: 15 } }] : []),
    ],
  } }));
  await page.route('**/api/marketplace/quotations/quote-real-1/select', route => { selected = true; return route.fulfill({ json: { quotation_id: 'quote-real-1', application_id: 'app-1', status: 'selected' } }); });
}

test('member compares and selects ranked real provider quotations', async ({ page }) => {
  await stubMemberMarketplace(page);
  await page.goto('/login');
  await page.getByLabel('Email address').fill('member@example');
  await page.getByLabel('Password').fill('password');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/\/(app|provider)$/);
  await page.goto('/app/marketplace/case-1');
  await expect(page.getByRole('heading', { name: 'Your provider quotations' })).toBeVisible();
  await expect(page.getByText('AED 8,200.00')).toBeVisible();
  await page.getByRole('button', { name: /Choose this quotation/ }).first().click();
  await expect(page.getByRole('heading', { name: 'Choose Al Noor Takaful?' })).toBeFocused();
  await page.getByRole('button', { name: 'Yes, confirm this policy' }).click();
  await expect(page.getByText(/Your choice was sent to the provider/)).toBeVisible();
  await expect(page.locator('[aria-current="step"]')).toContainText('Choice sent');
  await page.screenshot({ path: 'PIVOT_V2_PHASE7_MEMBER_TIMELINE.png', fullPage: true });
});

test('member sees partial replies and every persisted activation step at a narrow width', async ({ page }) => {
  await stubMemberMarketplace(page);
  await page.setViewportSize({ width: 320, height: 844 });
  let stage = 'quotation_received';
  const quote = { rank: 1, quotation_id: 'quote-real-1', provider_name: 'Emirates International Family Health Assurance', premium_aed: 8200, name: 'Family care', status: 'accepted', explanation: 'Submitted provider terms.', terms: { network: 'wide', maternity: { covered: false }, chronic_preexisting: { covered: true, waiting_period_months: 0 } } };
  await page.route('**/api/marketplace/cases/case-1/quotations', route => route.fulfill({ json: {
    status: stage, invited: 3, responded: stage === 'quotation_received' ? 1 : 3,
    collection_ready: stage !== 'quotation_received', collection_window_hours: 72,
    quotations: stage === 'quotation_received' ? [] : [quote], updates: [quote],
  } }));
  await page.goto('/login');
  await page.getByLabel('Email address').fill('member@example');
  await page.getByLabel('Password').fill('password');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/\/app$/);
  await page.goto('/app/marketplace/case-1');
  await expect(page.getByText('1 of 3 selected providers have responded.', { exact: false })).toBeVisible();
  await expect(page.getByRole('button', { name: /Choose this quotation/ })).toHaveCount(0);
  for (const [status, label] of [['provider_accepted', 'Provider accepted'], ['broker_final_review', 'Final review complete'], ['bound', 'Policy started']]) {
    stage = status;
    await page.reload();
    await expect(page.locator('[aria-current="step"]')).toContainText(label);
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);
  }
  await expect(page.getByRole('link', { name: 'Open policies & cover' })).toBeVisible();
});
