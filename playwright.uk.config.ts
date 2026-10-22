import { defineConfig } from '@playwright/test';
import { existsSync } from 'node:fs';
const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
export default defineConfig({
  testDir: './tests/uk', timeout: 60_000, workers: 1,
  reporter: [['list'], ['json', { outputFile: 'docs/uk/evidence/playwright.json' }]],
  use: { baseURL: 'http://127.0.0.1:4173', trace: 'retain-on-failure',
    launchOptions: existsSync(chrome) ? { executablePath: chrome } : undefined },
  webServer: [
    { command: 'npm --prefix frontend run dev -- --port 4173', url: 'http://127.0.0.1:4173', reuseExistingServer: !process.env.CI },
    { command: process.env.UK_TEST_PYTHON ? `"${process.env.UK_TEST_PYTHON}" backend/scripts/uk_test_server.py` : 'uv run --project backend python backend/scripts/uk_test_server.py', url: 'http://127.0.0.1:8000/health', reuseExistingServer: !process.env.CI, timeout: 120_000 },
  ],
});
