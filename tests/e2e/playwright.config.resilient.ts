import { defineConfig, devices } from '@playwright/test';

/**
 * Resilient test configuration with enhanced timeout handling
 */
export default defineConfig({
  testDir: './tests',
  
  // Increase parallelism for faster execution
  fullyParallel: true,
  workers: process.env.CI ? 2 : 4,
  
  // Retry failed tests
  retries: process.env.CI ? 3 : 2,
  
  // Test timeout settings
  timeout: 90 * 1000, // 90 seconds per test
  expect: {
    timeout: 15 * 1000, // 15 seconds for assertions
  },
  
  // Global settings
  use: {
    // Base URL - try multiple ports
    baseURL: process.env.BASE_URL || 'http://localhost:5173',
    
    // Trace and screenshot settings
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    
    // Timeouts
    actionTimeout: 20 * 1000, // 20 seconds for actions
    navigationTimeout: 45 * 1000, // 45 seconds for navigation
    
    // Viewport
    viewport: { width: 1280, height: 720 },
    
    // Ignore HTTPS errors (for local testing)
    ignoreHTTPSErrors: true,
    
    // Extra HTTP headers
    extraHTTPHeaders: {
      'Accept': 'application/json, text/plain, */*',
      'Accept-Language': 'en-US,en;q=0.9',
    },
  },
  
  // Projects with different strategies
  projects: [
    {
      name: 'chromium-fast',
      use: { 
        ...devices['Desktop Chrome'],
        // Faster timeouts for quick tests
        actionTimeout: 10 * 1000,
        navigationTimeout: 20 * 1000,
      },
      testMatch: '**/test_pdf_loader_local.spec.ts',
    },
    {
      name: 'chromium-resilient',
      use: { 
        ...devices['Desktop Chrome'],
        // Longer timeouts for external URLs
        actionTimeout: 30 * 1000,
        navigationTimeout: 60 * 1000,
      },
      testMatch: '**/test_pdf_loader.spec.ts',
    },
    {
      name: 'firefox-resilient',
      use: { 
        ...devices['Desktop Firefox'],
        actionTimeout: 30 * 1000,
        navigationTimeout: 60 * 1000,
      },
      testMatch: '**/test_*.spec.ts',
    },
  ],
  
  // Reporter configuration
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  
  // Web server configuration with health checks
  webServer: [
    {
      command: 'cd backend && uvicorn app.main:app --reload --port 8000',
      port: 8000,
      timeout: 120 * 1000,
      reuseExistingServer: true,
      // Health check
      healthCheck: async (axios) => {
        try {
          const response = await axios.get('http://localhost:8000/api/health');
          return response.data.status === 'healthy';
        } catch {
          return false;
        }
      },
    },
    {
      command: 'cd frontend && npm run dev -- --port 5173',
      port: 5173,
      timeout: 60 * 1000,
      reuseExistingServer: true,
      // Simple check for frontend
      healthCheck: async (axios) => {
        try {
          await axios.get('http://localhost:5173');
          return true;
        } catch {
          return false;
        }
      },
    },
  ],
});