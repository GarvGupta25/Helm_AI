import { expect, test, type Page } from './support';

async function signIn(page: Page, role: string, access?: (route: any) => Promise<void>) {
  await page.route('**/auth/v1/**', route => route.fulfill({ json: {
    access_token: 'portal-test-token', refresh_token: 'portal-test-refresh', expires_in: 3600,
    token_type: 'bearer', user: { id: 'portal-test-user', email: 'portal@example.test', app_metadata: {} },
  } }));
  await page.route('**/api/config', route => route.fulfill({ json: {
    auth_configured: true, supabase_url: 'http://127.0.0.1:54321', supabase_anon_key: 'local-demo-key',
    ai_available: false, voice_available: false, payment_provider: 'simulator',
  } }));
  await page.route('**/api/me/access', access || (route => route.fulfill({ json: { role } })));
  await page.goto('/login');
  await page.getByLabel('Email address').fill('portal@example.test');
  await page.getByLabel('Password').fill('test-password');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page).toHaveURL(/\/app$/);
}

for (const [role, name, variable] of [
  ['broker', 'Broker', 'VITE_BROKER_PORTAL_URL'],
  ['provider', 'Provider', 'VITE_PROVIDER_PORTAL_URL'],
  ['staff', 'Staff', 'VITE_STAFF_PORTAL_URL'],
]) {
  test(`${role} receives portal guidance without loading customer or internal data`, async ({ page }) => {
    const forbidden: string[] = [];
    page.on('request', request => {
      const path = new URL(request.url()).pathname;
      if (path.startsWith('/api/') && !['/api/config', '/api/me/access'].includes(path)) forbidden.push(path);
    });
    await signIn(page, role);
    await expect(page.getByRole('heading', { name: `Please use the ${name} portal.` })).toBeVisible();
    await expect(page.getByRole('navigation')).toHaveCount(0);
    const configured = process.env[variable]?.trim();
    if (configured && /^https?:\/\//.test(configured)) {
      await expect(page.getByRole('link', { name: `Open ${name} portal` })).toHaveAttribute('href', new URL(configured).href);
    } else {
      await expect(page.getByText('The portal address has not been configured.', { exact: false })).toBeVisible();
      await expect(page.getByRole('link', { name: `Open ${name} portal` })).toHaveCount(0);
    }
    expect(forbidden).toEqual([]);
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await expect(page).toHaveURL(/\/$/);
  });
}

test('customer pages wait for the authoritative account role', async ({ page }) => {
  let release!: () => void;
  const pending = new Promise<void>(resolve => { release = resolve; });
  const memberRequests: string[] = [];
  page.on('request', request => {
    const path = new URL(request.url()).pathname;
    if (['/api/policies', '/api/cases', '/api/me/profile'].includes(path)) memberRequests.push(path);
  });
  await signIn(page, 'member', async route => { await pending; await route.fulfill({ json: { role: 'member' } }); });
  await expect(page.getByRole('link', { name: 'Overview', exact: true })).toHaveCount(0);
  expect(memberRequests).toEqual([]);
  release();
  await expect(page.getByRole('link', { name: 'Overview', exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: /Broker workspace|Provider workspace|Claim review/ })).toHaveCount(0);
});

test('an account access failure has retry and sign-out without opening customer data', async ({ page }) => {
  let failed = true;
  await signIn(page, 'member', route => route.fulfill(failed
    ? { status: 503, json: { message: 'Account access temporarily unavailable.' } }
    : { json: { role: 'member' } }));
  await expect(page.getByRole('heading', { name: 'We could not check your account access.' })).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole('link', { name: 'Overview', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Sign out', exact: true })).toBeVisible();
  failed = false;
  await page.getByRole('button', { name: 'Try again', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Overview', exact: true })).toBeVisible();
});

test('archived workspace routes fall back to the public website', async ({ page }) => {
  await page.route('**/api/config', route => route.fulfill({ json: {
    auth_configured: false, supabase_url: '', supabase_anon_key: '', ai_available: false,
    voice_available: false, payment_provider: 'simulator',
  } }));
  for (const path of ['/app/broker', '/app/broker/claims', '/broker/claims', '/provider']) {
    await page.goto(path);
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole('heading', { name: 'Individual health cover for UAE residents.' })).toBeVisible();
  }
});
