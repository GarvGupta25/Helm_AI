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

test('broker UI fixture reviews a case, edits a draft and approves exact revision', async ({ page }) => {
  // UI-only fixture. Real role/assignment/approval enforcement is tested against FastAPI separately.
  const profile = { people: [{ relationship: 'lead_adult', age_years: 35 }], location: { region: 'England' }, cover: { start_date: '2026-12-01' },
    budget: { monthly_pence: 15000, strict: true }, excess: { max_pence: 50000, strict: false }, benefits: { required: ['outpatient'], preferred: ['physio'] } };
  const data = { id: 'case-ui-fixture', state: 'in_progress', version: 3, profile_version: 1, expires_at: '2026-12-02T12:00:00Z', urgency: 'normal', notice: 'UI fixture', profile,
    selected: [], contacts: [{ id: 'contact-ui-fixture', channel: 'email', destination: 'visitor@example.test', verified_in_demo: true }],
    preferences: { channels: ['dashboard'], quiet_start: 22, quiet_end: 8, time_zone: 'Europe/London' }, questions: [], notes: [], messages: [], audit: [], consents: [],
    documents: [] as { id: string; kind: string; revision: number; hash: string; ai_drafted: boolean; approved: boolean; draft: { text: string; audience: string; recipients: string[]; sources: string[] } }[], allowed_states: ['ready_for_signoff', 'closed'] };
  await page.route('**/api/config', route => route.fulfill({ json: { auth_configured: true, supabase_url: 'http://127.0.0.1:54321', supabase_anon_key: 'ui-fixture-public-key' } }));
  const user = { id: 'ui-fixture-broker', aud: 'authenticated', role: 'authenticated', email: 'broker@example.test', app_metadata: {}, user_metadata: {}, created_at: '2026-01-01T00:00:00Z' };
  const payload = Buffer.from(JSON.stringify({ sub: user.id, exp: Math.floor(Date.now()/1000)+3600 })).toString('base64url');
  const token = Buffer.from('{}').toString('base64url')+'.'+payload+'.fixture-signature';
  await page.route('**/auth/v1/**', route => route.fulfill({ json: { access_token: token, token_type: 'bearer', expires_in: 3600, refresh_token: 'ui-fixture-refresh', user } }));
  await page.route('**/api/journey/broker/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/me')) return route.fulfill({ json: { id: user.id, role: 'broker' } });
    if (path.endsWith('/assistant/queue') || path.endsWith('/inbox')) return route.fulfill({ json: { items: [] } });
    if (path.endsWith('/assistant')) return route.fulfill({ json: { notice: 'Prototype review prompts pending legal review.', checklist_version: 'demo-review-v1', checklist: [{id:'profile', label:'Review confirmed needs', source:'profile', status:'missing'}], statements: [{text:'Source not yet supplied',source:'profile.people',confidence:'review'}], next_deadline: data.expires_at, prepared_documents: [] } });
    if (path.endsWith('/cases')) return route.fulfill({ json: { total: 1, items: [data] } });
    if (route.request().method() === 'POST') {
      const body = route.request().postDataJSON();
      if (path.endsWith('/documents')) data.documents.push({ id: 'doc-ui-fixture', kind: 'case_summary', revision: 1, hash: '0'.repeat(64), ai_drafted: true, approved: false, draft: { text: 'Internal synthetic draft for human review.', audience: 'customer', recipients: ['contact-ui-fixture'], sources: ['profile:1'] } });
      if (path.endsWith('/edit')) { data.documents[0].draft.text = body.text; data.documents[0].revision++; data.documents[0].approved = false; }
      if (path.endsWith('/transition')) data.state = body.state;
      if (path.endsWith('/review')) data.documents[0].approved = body.decision === 'approve';
      if (path.endsWith('/dispatch')) data.state = 'submitted';
      data.version++;
    }
    return route.fulfill({ json: data });
  });
  await page.goto('/broker.html');
  await page.getByLabel('Work email', { exact: true }).fill(user.email);
  await page.getByLabel('Password', { exact: true }).fill('ui-fixture-only');
  await page.getByRole('button', { name: 'Sign in securely' }).click();
  await expect(page.getByRole('heading', { name: 'Your case queue' })).toBeVisible();
  await page.getByRole('button', { name: /case-ui-/ }).click();
  await expect(page.getByRole('heading', { name: 'Profile & priorities' })).toBeVisible();
  await page.getByRole('tab', { name: 'assistant', exact: true }).click();
  await expect(page.getByText('Human clarification needed', { exact: false })).toBeVisible();
  await page.getByRole('tab', { name: 'documents', exact: true }).click();
  await page.getByRole('button', { name: 'Prepare internal demo draft' }).click();
  await expect(page.getByRole('button', { name: 'Simulate approved delivery' })).toBeDisabled();
  await page.getByLabel('Review document text', { exact: true }).fill('Human-reviewed synthetic draft. No policy or payment.');
  await page.getByRole('button', { name: 'Save a new revision' }).click();
  await expect(page.getByRole('heading', { name: 'case summary · Revision 2' })).toBeVisible();
  await page.getByRole('tab', { name: 'overview', exact: true }).click();
  await page.getByLabel('Move case to', { exact: true }).selectOption('ready_for_signoff');
  await page.getByRole('checkbox', { name: /I reviewed profile/ }).check();
  await page.getByRole('button', { name: 'Update case', exact: true }).click();
  await page.getByRole('tab', { name: 'documents', exact: true }).click();
  await page.getByRole('checkbox', { name: /I reviewed this exact text/ }).check();
  await page.getByRole('button', { name: 'Approve exact revision', exact: true }).click();
  await expect(page.getByText('Exact revision approved', { exact: true })).toBeVisible();
  const scan = await new AxeBuilder({ page }).include('.b-main').analyze();
  expect(scan.violations.filter(v => ['serious', 'critical'].includes(v.impact || ''))).toEqual([]);
  await page.getByRole('button', { name: 'Simulate approved delivery', exact: true }).click();
  await expect(page.getByText('Simulated dispatch', { exact: true })).toBeVisible();
  await page.setViewportSize({ width: 375, height: 900 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
});
