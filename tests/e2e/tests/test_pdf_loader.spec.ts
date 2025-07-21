import { test, expect } from '@playwright/test';
import { UploadPage } from '../pages/UploadPage';
import { ViewerPage } from '../pages/ViewerPage';
import { SAMPLE_PDFS } from '../fixtures/sample-pdfs';
import { 
  waitForAPIResponse, 
  waitForElementReady, 
  retryWithBackoff,
  waitForPDFLoad,
  waitForLoadingComplete 
} from '../helpers/wait-helpers';

test.describe('Test PDF Loader Feature', () => {
  let uploadPage: UploadPage;
  let viewerPage: ViewerPage;

  test.beforeEach(async ({ page }) => {
    uploadPage = new UploadPage(page);
    viewerPage = new ViewerPage(page);
    await uploadPage.goto();
  });

  test('should display test PDF loader button', async ({ page }) => {
    // Look for the test PDF loader button
    const loaderButton = page.locator('button:has-text("Load Test PDF")');
    await expect(loaderButton).toBeVisible();
    
    // Check that it has the correct icon
    await expect(loaderButton.locator('svg')).toBeVisible();
  });

  test('should open dropdown menu with sample PDFs', async ({ page }) => {
    // Click the loader button
    const loaderButton = page.locator('button:has-text("Load Test PDF")');
    await loaderButton.click();
    
    // Check that the menu is visible
    const menu = page.locator('[role="menu"]');
    await expect(menu).toBeVisible();
    
    // Verify all sample PDFs are listed
    for (const samplePDF of SAMPLE_PDFS) {
      await expect(menu.locator(`text=${samplePDF.name}`)).toBeVisible();
    }
    
    // Check for the description text
    await expect(menu.locator('text=Sample PDFs for Testing')).toBeVisible();
  });

  test('should load EPA sample PDF', async ({ page }) => {
    // Ensure we're on the right port
    const currentUrl = page.url();
    if (!currentUrl.includes(':5173')) {
      await page.goto('http://localhost:5173');
    }
    
    // Wait for loader button and click
    await waitForElementReady(page, 'button:has-text("Load Test PDF")');
    await page.locator('button:has-text("Load Test PDF")').click();
    
    // Wait for menu to be visible before clicking
    await waitForElementReady(page, 'text=EPA Sample Letter');
    await page.locator('text=EPA Sample Letter').click();
    
    // Wait for API response with retry
    const responsePromise = waitForAPIResponse(page, '/api/load-url', {
      timeout: 45000,
      predicate: (response) => response.status() === 200
    });
    
    const response = await responsePromise;
    
    // Check for success message with retry
    await retryWithBackoff(async () => {
      await expect(page.locator('text=Successfully loaded: EPA Sample Letter')).toBeVisible({
        timeout: 10000
      });
    });
    
    // Wait for loading to complete
    await waitForLoadingComplete(page);
    
    // Wait for PDF to be fully loaded
    await waitForPDFLoad(page, { timeout: 30000 });
    
    // Verify PDF is displayed
    await retryWithBackoff(async () => {
      expect(await viewerPage.isPDFVisible()).toBeTruthy();
    });
    
    // Verify it's a 3-page document (EPA sample has 3 pages)
    await retryWithBackoff(async () => {
      const totalPages = await viewerPage.getTotalPages();
      expect(totalPages).toBe(3);
    }, { maxAttempts: 3, initialDelay: 1000 });
  });

  test('should load NHTSA form PDF', async ({ page }) => {
    // Click the loader button
    await page.locator('button:has-text("Load Test PDF")').click();
    
    // Click on NHTSA form
    await page.locator('text=NHTSA Form').click();
    
    // Wait for loading to complete
    await page.waitForResponse(response => 
      response.url().includes('/api/load-url') && response.status() === 200
    );
    
    // Check for success message
    await expect(page.locator('text=Successfully loaded: NHTSA Form')).toBeVisible();
    
    // Wait for PDF viewer to load
    await viewerPage.waitForPDFLoad();
    
    // Verify PDF is displayed
    expect(await viewerPage.isPDFVisible()).toBeTruthy();
  });

  test('should handle loading errors gracefully', async ({ page, context }) => {
    // Intercept the API call and make it fail
    await context.route('**/api/load-url', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Failed to download PDF' })
      });
    });
    
    // Click the loader button
    await page.locator('button:has-text("Load Test PDF")').click();
    
    // Click on any sample
    await page.locator('text=EPA Sample Letter').click();
    
    // Check for error message
    await expect(page.locator('text=Failed to download PDF')).toBeVisible();
    
    // Verify we're still on the upload page
    await expect(page.locator('text=Drop your PDF here')).toBeVisible();
  });

  test('should show loading state during download', async ({ page }) => {
    // Slow down the response to see loading state
    await page.route('**/api/load-url', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.continue();
    });
    
    // Click the loader button
    await page.locator('button:has-text("Load Test PDF")').click();
    
    // Click on a sample
    await page.locator('text=Anyline Sample Book').click();
    
    // Check for loading state
    const loaderButton = page.locator('button:has-text("Load Test PDF")');
    await expect(loaderButton).toBeDisabled();
    
    // The button should show a loading spinner
    await expect(loaderButton.locator('[role="progressbar"]')).toBeVisible();
  });

  test('should load all sample PDFs successfully', async ({ page }) => {
    for (const samplePDF of SAMPLE_PDFS) {
      // Click the loader button
      await page.locator('button:has-text("Load Test PDF")').click();
      
      // Click on the sample
      await page.locator(`text=${samplePDF.name}`).click();
      
      // Wait for loading to complete
      await page.waitForResponse(response => 
        response.url().includes('/api/load-url') && response.status() === 200
      );
      
      // Check for success message
      await expect(page.locator(`text=Successfully loaded: ${samplePDF.name}`)).toBeVisible();
      
      // Wait for PDF viewer to load
      await viewerPage.waitForPDFLoad();
      
      // Verify PDF is displayed
      expect(await viewerPage.isPDFVisible()).toBeTruthy();
      
      // Go back to upload page for next test
      if (samplePDF !== SAMPLE_PDFS[SAMPLE_PDFS.length - 1]) {
        await uploadPage.goto();
      }
    }
  });
});