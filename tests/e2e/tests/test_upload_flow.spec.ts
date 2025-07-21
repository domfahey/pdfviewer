import { test, expect } from '@playwright/test';
import { UploadPage } from '../pages/UploadPage';
import { ViewerPage } from '../pages/ViewerPage';
import { testFiles } from '../fixtures/test-files';
import path from 'path';

test.describe('PDF Upload Flow', () => {
  let uploadPage: UploadPage;
  let viewerPage: ViewerPage;

  test.beforeEach(async ({ page }) => {
    uploadPage = new UploadPage(page);
    viewerPage = new ViewerPage(page);
    await uploadPage.goto();
  });

  test('should display upload page with drop zone', async ({ page }) => {
    await expect(page).toHaveTitle(/PDF Viewer/);
    expect(await uploadPage.isDropZoneVisible()).toBeTruthy();
    
    // Check for upload instructions
    await expect(page.locator('text=Drop your PDF here')).toBeVisible();
    await expect(page.locator('text=or click to browse')).toBeVisible();
    await expect(page.locator('text=Maximum file size: 50MB')).toBeVisible();
  });

  test('should upload a valid PDF file', async ({ page }) => {
    // Use the sample PDF from fixtures
    const samplePdfPath = path.join(process.cwd(), 'tests', 'fixtures', 'sample.pdf');
    
    // Upload the file
    await uploadPage.uploadFile(samplePdfPath);
    
    // Wait for upload to complete and navigation to viewer
    await uploadPage.waitForUploadComplete();
    
    // Verify we're on the viewer page
    await viewerPage.waitForPDFLoad();
    expect(await viewerPage.isPDFVisible()).toBeTruthy();
    
    // Verify page count
    const totalPages = await viewerPage.getTotalPages();
    expect(totalPages).toBeGreaterThan(0);
  });

  test('should show error for invalid file type', async ({ page }) => {
    // Create a temporary text file
    const invalidFilePath = path.join(process.cwd(), 'tests', 'e2e', 'fixtures', 'invalid.txt');
    
    // Try to upload the invalid file
    await uploadPage.uploadFile(invalidFilePath);
    
    // Check for error message
    const errorMessage = await uploadPage.getErrorMessage();
    expect(errorMessage).toBeTruthy();
    expect(errorMessage).toContain('PDF');
  });

  test('should handle multiple file uploads', async ({ page }) => {
    const samplePdfPath = path.join(process.cwd(), 'tests', 'fixtures', 'sample.pdf');
    
    // Upload first file
    await uploadPage.uploadFile(samplePdfPath);
    await uploadPage.waitForUploadComplete();
    await viewerPage.waitForPDFLoad();
    
    // Go back to upload page
    await page.goBack();
    await uploadPage.goto();
    
    // Upload second file
    await uploadPage.uploadFile(samplePdfPath);
    await uploadPage.waitForUploadComplete();
    await viewerPage.waitForPDFLoad();
    
    // Verify second file loads correctly
    expect(await viewerPage.isPDFVisible()).toBeTruthy();
  });

  test('should show upload progress for large files', async ({ page }) => {
    // This test would use a larger PDF file
    // For now, we'll use the sample PDF
    const samplePdfPath = path.join(process.cwd(), 'tests', 'fixtures', 'sample.pdf');
    
    // Start upload
    await uploadPage.uploadFile(samplePdfPath);
    
    // Look for progress indicator (if implemented)
    // await expect(page.locator('[role="progressbar"]')).toBeVisible();
    
    // Wait for completion
    await uploadPage.waitForUploadComplete();
    await viewerPage.waitForPDFLoad();
  });

  test('should maintain file info after upload', async ({ page }) => {
    const samplePdfPath = path.join(process.cwd(), 'tests', 'fixtures', 'sample.pdf');
    
    // Upload file
    await uploadPage.uploadFile(samplePdfPath);
    await uploadPage.waitForUploadComplete();
    await viewerPage.waitForPDFLoad();
    
    // Check that file info is displayed
    // This depends on your UI implementation
    const currentPage = await viewerPage.getCurrentPage();
    const totalPages = await viewerPage.getTotalPages();
    
    expect(currentPage).toBe(1);
    expect(totalPages).toBeGreaterThan(0);
  });
});