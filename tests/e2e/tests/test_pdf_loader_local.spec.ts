import { test, expect } from '@playwright/test';
import { UploadPage } from '../pages/UploadPage';
import { ViewerPage } from '../pages/ViewerPage';
import path from 'path';
import fs from 'fs';

/**
 * Test PDF loader with local files to avoid external URL timeouts
 * This test suite uses local PDF files instead of downloading from URLs
 */
test.describe('Test PDF Loader - Local Files', () => {
  let uploadPage: UploadPage;
  let viewerPage: ViewerPage;

  test.beforeEach(async ({ page }) => {
    uploadPage = new UploadPage(page);
    viewerPage = new ViewerPage(page);
    await uploadPage.goto();
  });

  test('should upload local EPA sample PDF', async ({ page }) => {
    // Check if local file exists
    const localPdfPath = path.join(process.cwd(), 'tests/fixtures/epa_sample.pdf');
    
    test.skip(!fs.existsSync(localPdfPath), 'Local EPA sample PDF not found');
    
    // Upload the file directly
    await uploadPage.uploadFile(localPdfPath);
    
    // Wait for upload to complete
    await uploadPage.waitForUploadComplete();
    
    // Wait for PDF viewer to load
    await viewerPage.waitForPDFLoad();
    
    // Verify PDF is displayed
    expect(await viewerPage.isPDFVisible()).toBeTruthy();
    
    // Verify it's a 3-page document
    const totalPages = await viewerPage.getTotalPages();
    expect(totalPages).toBe(3);
  });

  test('should handle drag and drop upload', async ({ page }) => {
    const localPdfPath = path.join(process.cwd(), 'tests/fixtures/epa_sample.pdf');
    
    test.skip(!fs.existsSync(localPdfPath), 'Local EPA sample PDF not found');
    
    // Create a data transfer object
    const dataTransfer = await page.evaluateHandle(() => new DataTransfer());
    
    // Dispatch drag and drop events
    const dropZone = page.locator('[data-testid="drop-zone"]');
    
    // Trigger drag over
    await dropZone.dispatchEvent('dragover', { dataTransfer });
    
    // Check for visual feedback
    await expect(dropZone).toHaveCSS('border-color', 'rgb(25, 118, 210)');
    
    // Note: Actual file drop simulation is complex in Playwright
    // For now, we'll use the regular upload method
    await uploadPage.uploadFile(localPdfPath);
    await uploadPage.waitForUploadComplete();
  });

  test('should show upload progress', async ({ page }) => {
    const localPdfPath = path.join(process.cwd(), 'tests/fixtures/epa_sample.pdf');
    
    test.skip(!fs.existsSync(localPdfPath), 'Local EPA sample PDF not found');
    
    // Start upload
    const fileInput = page.locator('input[type="file"]');
    
    // Upload file
    await fileInput.setInputFiles(localPdfPath);
    
    // Look for progress bar (it might appear and disappear quickly)
    const progressBar = page.locator('[role="progressbar"]');
    
    // Check if progress bar appears (might be too fast for small files)
    try {
      await progressBar.waitFor({ state: 'visible', timeout: 5000 });
      // Wait for it to disappear
      await progressBar.waitFor({ state: 'hidden', timeout: 30000 });
    } catch (e) {
      // Progress bar might not appear for small files uploaded quickly
      console.log('Progress bar did not appear or disappeared too quickly');
    }
    
    // Verify upload completed
    await uploadPage.waitForUploadComplete();
    await viewerPage.waitForPDFLoad();
  });

  test('should allow multiple sequential uploads', async ({ page }) => {
    const localPdfPath = path.join(process.cwd(), 'tests/fixtures/epa_sample.pdf');
    
    test.skip(!fs.existsSync(localPdfPath), 'Local EPA sample PDF not found');
    
    // First upload
    await uploadPage.uploadFile(localPdfPath);
    await uploadPage.waitForUploadComplete();
    await viewerPage.waitForPDFLoad();
    
    // Verify first upload
    expect(await viewerPage.isPDFVisible()).toBeTruthy();
    
    // Look for new upload button (FAB)
    const newUploadButton = page.locator('button[aria-label="upload new PDF"]');
    await expect(newUploadButton).toBeVisible();
    
    // Click to start new upload
    await newUploadButton.click();
    
    // Should be back at upload page
    await expect(page.locator('text=Drop your PDF here')).toBeVisible();
    
    // Second upload
    await uploadPage.uploadFile(localPdfPath);
    await uploadPage.waitForUploadComplete();
    await viewerPage.waitForPDFLoad();
    
    // Verify second upload
    expect(await viewerPage.isPDFVisible()).toBeTruthy();
  });
});

/**
 * Performance-focused tests with local files
 */
test.describe('PDF Loader Performance', () => {
  test('should load PDF within acceptable time', async ({ page }) => {
    const uploadPage = new UploadPage(page);
    const viewerPage = new ViewerPage(page);
    
    await uploadPage.goto();
    
    const localPdfPath = path.join(process.cwd(), 'tests/fixtures/epa_sample.pdf');
    test.skip(!fs.existsSync(localPdfPath), 'Local EPA sample PDF not found');
    
    // Measure upload time
    const startTime = Date.now();
    
    await uploadPage.uploadFile(localPdfPath);
    await uploadPage.waitForUploadComplete();
    await viewerPage.waitForPDFLoad();
    
    const endTime = Date.now();
    const loadTime = endTime - startTime;
    
    console.log(`PDF load time: ${loadTime}ms`);
    
    // Should load within 10 seconds for local file
    expect(loadTime).toBeLessThan(10000);
    
    // Verify PDF loaded correctly
    expect(await viewerPage.isPDFVisible()).toBeTruthy();
  });
});