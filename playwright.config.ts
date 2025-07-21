import { defineConfig, devices } from '@playwright/test';

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */
// require('dotenv').config();

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  testDir: './tests/e2e',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 1,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/e2e-results.json' }],
    ['junit', { outputFile: 'test-results/e2e-results.xml' }],
  ],
  
  /* Global timeout for the whole test run */
  globalTimeout: 10 * 60 * 1000, // 10 minutes
  
  /* Timeout for each test */
  timeout: 60 * 1000, // 60 seconds per test
  
  /* Timeout for expect assertions */
  expect: {
    timeout: 10 * 1000, // 10 seconds for assertions
  },
  
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:5173',

    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',

    /* Screenshot on failure */
    screenshot: 'only-on-failure',

    /* Video on failure */
    video: 'retain-on-failure',
    
    /* Action timeout */
    actionTimeout: 15 * 1000, // 15 seconds for actions like click, fill
    
    /* Navigation timeout */
    navigationTimeout: 30 * 1000, // 30 seconds for page loads
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    /* Test against mobile viewports. */
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  /* Run your local dev server before starting the tests */
  webServer: [
    {
      command: 'cd backend && uvicorn app.main:app --reload --port 8000',
      port: 8000,
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
    {
      command: 'cd frontend && npm run dev -- --port 5173',
      port: 5173,
      reuseExistingServer: !process.env.CI,
      timeout: 60000,
    },
  ],
});