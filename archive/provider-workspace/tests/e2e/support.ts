import { test as base, expect, type Page } from '@playwright/test';

// These browser tests exercise the real UI against deterministic API boundaries.
// Backend authorization and persistence are covered by the API suite.
export const test = base.extend({
  page: async ({ page }, use) => {
    await page.route('**/api/**', route => {
      const path = new URL(route.request().url()).pathname;
      const payload = path === '/api/me/profile' ? { facts: {}, version: 1, readiness: { ready: false, missing: ['legal_name'] } }
        : path === '/api/public/marketplace-plans' ? { plans: [] }
          : path === '/api/public/marketplace-partners' ? { items: [] }
            : [];
      return route.fulfill({ json: payload });
    });
    await use(page);
  },
});
export { expect, type Page };
