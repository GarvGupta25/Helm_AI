import { test, expect } from './support';

test('broker can preview and download originals for emergency and regular claims', async ({ page }, info) => {
  await page.route('**/auth/v1/**', route => route.fulfill({ json: {
    access_token: 'broker-token', refresh_token: 'broker-refresh', expires_in: 3600,
    token_type: 'bearer', user: { id: 'broker-1', email: 'broker@example', app_metadata: { helm_role: 'broker' } },
  } }));
  await page.route('**/api/config', route => route.fulfill({ json: { auth_configured: true, supabase_url: 'http://127.0.0.1:54321', supabase_anon_key: 'local-demo-key', ai_available: false, voice_available: false, payment_provider: 'simulator' } }));
  await page.route('**/api/me/access', route => route.fulfill({ json: { role: 'broker' } }));
  await page.route('**/api/broker/claims/observability', route => route.fulfill({ json: { routes: {}, mean_seconds_to_decision: {}, false_auto_rate_pct: null, oncall_page_within_60_seconds: { met: 0, total: 0 } } }));
  await page.route('**/api/broker/claims', route => route.fulfill({ json: [true, false].map((emergency, index) => ({
    id: `claim-${index}`, created_at: '2026-10-20T09:00:00Z', is_emergency: emergency,
    intake: { kind: emergency ? 'emergency' : 'claim', raw_message: 'I need help with a bill.', structured_fields: { provider_name: 'Emirates International Hospital and Community Clinic — نور الهدى' } },
    policy: { id: 'policy-1', status: 'demo_active', plan: { name: 'Family care' } },
    claimant: { id: `member-${index}`, name: emergency ? 'Aleksandra Wiśniewska-Kowalczyk' : '王秀英' },
    documents: [{ id: `document-${index}`, doc_type: 'bill', extracted_fields: { file_name: 'Q3 Hospital Invoice — FINAL (reviewed) v12.pdf' }, completeness_ok: false, has_original: true }],
    flags: [{ id: `flag-${index}`, flag_type: 'missing_docs', reason: 'Human review of the supplied evidence is required.' }],
    transcript: [{ role: 'member', content: 'Please review the attached bill.' }], suggested_action: { action: 'request_more_information', reasoning: 'Verify the bill before a decision.' },
  })) }));
  await page.route('**/api/broker/claims/*/documents/*/original', route => {
    expect(route.request().headers().authorization).toBe('Bearer broker-token');
    return route.fulfill({ contentType: 'application/pdf', body: Buffer.from('%PDF-1.4\n% demo original\n%%EOF') });
  });
  await page.goto('/login');
  await page.getByLabel('Email address').fill('broker@example');
  await page.getByLabel('Password').fill('password');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/\/app$/);
  await page.goto('/app/broker/claims');
  for (const name of ['Aleksandra Wiśniewska-Kowalczyk', '王秀英']) {
    await page.getByRole('button', { name: new RegExp(name) }).click();
    await page.getByRole('button', { name: 'View original image or PDF' }).click();
    await expect(page.getByTitle('Uploaded claim PDF')).toHaveAttribute('src', /^blob:/);
    const downloaded = page.waitForEvent('download');
    await page.getByRole('link', { name: 'Download original' }).click();
    expect((await downloaded).suggestedFilename()).toBe('claim-document.pdf');
  }
  await page.setViewportSize({ width: 320, height: 900 });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await page.screenshot({ path: info.outputPath('broker-claim-review-320.png') });
});
