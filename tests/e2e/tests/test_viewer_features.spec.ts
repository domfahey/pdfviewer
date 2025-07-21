import { test, expect } from '@playwright/test';
import { UploadPage } from '../pages/UploadPage';
import { ViewerPage } from '../pages/ViewerPage';
import path from 'path';

test.describe('PDF Viewer Features', () => {
  let uploadPage: UploadPage;
  let viewerPage: ViewerPage;

  // Upload a PDF before each test
  test.beforeEach(async ({ page }) => {
    uploadPage = new UploadPage(page);
    viewerPage = new ViewerPage(page);
    
    // Navigate to upload page and upload a sample PDF
    await uploadPage.goto();
    const samplePdfPath = path.join(process.cwd(), 'tests', 'fixtures', 'sample.pdf');
    await uploadPage.uploadFile(samplePdfPath);
    await uploadPage.waitForUploadComplete();
    await viewerPage.waitForPDFLoad();
  });

  test('should navigate between pages', async ({ page }) => {
    // Get initial page info
    const initialPage = await viewerPage.getCurrentPage();
    const totalPages = await viewerPage.getTotalPages();
    
    expect(initialPage).toBe(1);
    
    if (totalPages > 1) {
      // Go to next page
      await viewerPage.nextPage();
      expect(await viewerPage.getCurrentPage()).toBe(2);
      
      // Go to previous page
      await viewerPage.previousPage();
      expect(await viewerPage.getCurrentPage()).toBe(1);
      
      // Go to specific page
      await viewerPage.goToPage(totalPages);
      expect(await viewerPage.getCurrentPage()).toBe(totalPages);
    }
  });

  test('should change zoom levels', async ({ page }) => {
    // Test different zoom levels
    const zoomLevels = ['50%', '100%', '150%', '200%'];
    
    for (const zoom of zoomLevels) {
      await viewerPage.setZoom(zoom);
      // Verify canvas size changes (would need to check actual dimensions)
      await expect(viewerPage.pdfCanvas).toBeVisible();
    }
  });

  test('should search within PDF', async ({ page }) => {
    // Perform a search
    await viewerPage.search('the');
    
    // Check search results
    const results = await viewerPage.getSearchResultsCount();
    
    // If results found, verify navigation
    if (results.total > 0) {
      expect(results.current).toBe(1);
      expect(results.total).toBeGreaterThan(0);
      
      // Check that search highlights are visible
      await expect(page.locator('mark, .highlight')).toBeVisible();
    }
  });

  test('should toggle thumbnails panel', async ({ page }) => {
    // Initially thumbnails should be hidden
    expect(await viewerPage.isThumbnailsPanelVisible()).toBeFalsy();
    
    // Toggle thumbnails
    await viewerPage.toggleThumbnails();
    expect(await viewerPage.isThumbnailsPanelVisible()).toBeTruthy();
    
    // Toggle again to hide
    await viewerPage.toggleThumbnails();
    expect(await viewerPage.isThumbnailsPanelVisible()).toBeFalsy();
  });

  test('should navigate using thumbnails', async ({ page }) => {
    const totalPages = await viewerPage.getTotalPages();
    
    if (totalPages > 1) {
      // Open thumbnails
      await viewerPage.toggleThumbnails();
      
      // Click on thumbnail for page 2
      await viewerPage.selectThumbnail(2);
      
      // Verify navigation
      expect(await viewerPage.getCurrentPage()).toBe(2);
    }
  });

  test('should rotate document', async ({ page }) => {
    // Get initial canvas dimensions
    const initialBox = await viewerPage.pdfCanvas.boundingBox();
    
    // Rotate document
    await viewerPage.rotateDocument();
    
    // Canvas should still be visible
    await expect(viewerPage.pdfCanvas).toBeVisible();
    
    // Dimensions might change after rotation
    const rotatedBox = await viewerPage.pdfCanvas.boundingBox();
    expect(rotatedBox).toBeTruthy();
  });

  test('should change fit modes', async ({ page }) => {
    // Test fit to width
    await viewerPage.setFitMode('width');
    await expect(viewerPage.pdfCanvas).toBeVisible();
    
    // Test fit to height
    await viewerPage.setFitMode('height');
    await expect(viewerPage.pdfCanvas).toBeVisible();
    
    // Test fit to page
    await viewerPage.setFitMode('page');
    await expect(viewerPage.pdfCanvas).toBeVisible();
  });

  test('should toggle between view modes', async ({ page }) => {
    // Initially should be in original mode
    await expect(viewerPage.pdfCanvas).toBeVisible();
    
    // Toggle to digital mode
    await viewerPage.toggleViewMode();
    
    // In digital mode, canvas might not be visible
    // Check for digital content instead
    await expect(page.locator('text=Digital view')).toBeVisible();
  });

  test('should handle keyboard shortcuts', async ({ page }) => {
    const totalPages = await viewerPage.getTotalPages();
    
    if (totalPages > 1) {
      // Test arrow key navigation
      await page.keyboard.press('ArrowRight');
      await page.waitForTimeout(500);
      expect(await viewerPage.getCurrentPage()).toBe(2);
      
      await page.keyboard.press('ArrowLeft');
      await page.waitForTimeout(500);
      expect(await viewerPage.getCurrentPage()).toBe(1);
    }
    
    // Test zoom shortcuts
    await page.keyboard.press('+');
    await page.waitForTimeout(500);
    await expect(viewerPage.pdfCanvas).toBeVisible();
    
    await page.keyboard.press('-');
    await page.waitForTimeout(500);
    await expect(viewerPage.pdfCanvas).toBeVisible();
  });

  test('should handle window resize', async ({ page }) => {
    // Set initial viewport
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.waitForTimeout(500);
    await expect(viewerPage.pdfCanvas).toBeVisible();
    
    // Resize to mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);
    await expect(viewerPage.pdfCanvas).toBeVisible();
    
    // Resize back to desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(500);
    await expect(viewerPage.pdfCanvas).toBeVisible();
  });
});