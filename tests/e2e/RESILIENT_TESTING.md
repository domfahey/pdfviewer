# Resilient E2E Testing Guide

This guide provides best practices for writing E2E tests that are resilient to timeouts and network issues.

## Common Timeout Issues and Solutions

### 1. External URL Dependencies
**Problem**: Tests fail when downloading PDFs from external URLs due to network issues.

**Solutions**:
- Use local PDF files when possible
- Implement retry logic with exponential backoff
- Use mock servers for predictable behavior
- Set appropriate timeout values (60s+ for external resources)

### 2. Dynamic Port Allocation
**Problem**: Frontend dev server starts on different ports (5173, 5174, etc.)

**Solutions**:
- Check current URL and navigate to correct port
- Use `baseURL` configuration in Playwright
- Implement port detection logic
- Use `reuseExistingServer: true` in config

### 3. Async Loading States
**Problem**: Tests fail because they don't wait for loading to complete.

**Solutions**:
- Use custom wait helpers (`waitForLoadingComplete`)
- Wait for specific elements to appear/disappear
- Check for loading indicators before proceeding
- Use `waitForFunction` for complex conditions

## Best Practices

### 1. Use Explicit Waits
```typescript
// Bad
await page.waitForTimeout(5000); // Arbitrary wait

// Good
await waitForElementReady(page, 'button:has-text("Load Test PDF")');
await waitForLoadingComplete(page);
```

### 2. Implement Retry Logic
```typescript
await retryWithBackoff(async () => {
  const totalPages = await viewerPage.getTotalPages();
  expect(totalPages).toBe(3);
}, { 
  maxAttempts: 3, 
  initialDelay: 1000 
});
```

### 3. Handle Network Failures Gracefully
```typescript
const response = await waitForAPIResponse(page, '/api/load-url', {
  timeout: 45000,
  predicate: (response) => response.status() === 200
});
```

### 4. Use Test Fixtures
- Download test PDFs once and reuse them
- Create local copies of external resources
- Use mock servers for consistent behavior

### 5. Configure Appropriate Timeouts
```typescript
// playwright.config.ts
export default defineConfig({
  timeout: 90 * 1000, // 90s per test
  expect: { timeout: 15 * 1000 }, // 15s for assertions
  use: {
    actionTimeout: 20 * 1000, // 20s for actions
    navigationTimeout: 45 * 1000, // 45s for navigation
  },
});
```

### 6. Skip Tests When Prerequisites Fail
```typescript
test.skip(!fs.existsSync(localPdfPath), 'Local PDF not found');
```

### 7. Use Parallel Execution Wisely
- Run independent tests in parallel
- Use serial mode for dependent tests
- Limit workers on CI to avoid resource issues

### 8. Implement Health Checks
```typescript
webServer: {
  healthCheck: async (axios) => {
    const response = await axios.get('http://localhost:8000/api/health');
    return response.data.status === 'healthy';
  },
}
```

## Running Resilient Tests

### Local Development
```bash
# Run with local files only
npx playwright test test_pdf_loader_local.spec.ts

# Run with resilient config
npx playwright test --config=playwright.config.resilient.ts

# Run specific test with retries
npx playwright test -g "should load EPA sample PDF" --retries=3
```

### CI/CD
```bash
# Set environment variables
export CI=true
export BASE_URL=http://localhost:5173

# Run with increased timeouts
npx playwright test --timeout=120000

# Run with specific reporter
npx playwright test --reporter=json
```

## Debugging Timeout Issues

### 1. Enable Debug Mode
```bash
DEBUG=pw:api npx playwright test
```

### 2. Use Trace Viewer
```bash
npx playwright test --trace on
npx playwright show-trace trace.zip
```

### 3. Increase Verbosity
```bash
npx playwright test --reporter=list --verbose
```

### 4. Test in Headed Mode
```bash
npx playwright test --headed --slow-mo=1000
```

## Common Patterns

### Wait for PDF to Load
```typescript
await waitForPDFLoad(page, { timeout: 30000 });
```

### Handle Loading States
```typescript
await waitForLoadingComplete(page);
```

### Retry Failed Assertions
```typescript
await retryWithBackoff(async () => {
  expect(await viewerPage.isPDFVisible()).toBeTruthy();
});
```

### Check Multiple Ports
```typescript
const ports = [5173, 5174, 5175, 5176];
for (const port of ports) {
  try {
    await page.goto(`http://localhost:${port}`);
    break;
  } catch {
    continue;
  }
}
```

## Monitoring Test Reliability

### Track Flaky Tests
- Use test reporting to identify flaky tests
- Add retries for known flaky tests
- Fix root causes when possible

### Measure Test Duration
- Monitor test execution time
- Optimize slow tests
- Set appropriate timeout budgets

### Review Failure Patterns
- Network timeouts → Add retries
- Element not found → Add explicit waits
- Port conflicts → Use dynamic port detection