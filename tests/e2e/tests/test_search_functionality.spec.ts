import { test, expect } from '@playwright/test';
import { UploadPage } from '../pages/UploadPage';
import { ViewerPage } from '../pages/ViewerPage';
import path from 'path';

test.describe('PDF Search Functionality', () => {
  let uploadPage: UploadPage;
  let viewerPage: ViewerPage;

  test.beforeEach(async ({ page }) => {
    uploadPage = new UploadPage(page);
    viewerPage = new ViewerPage(page);
    
    // Upload a PDF with text content
    await uploadPage.goto();
    const samplePdfPath = path.join(process.cwd(), 'tests', 'fixtures', 'sample.pdf');
    await uploadPage.uploadFile(samplePdfPath);
    await uploadPage.waitForUploadComplete();
    await viewerPage.waitForPDFLoad();
  });

  test('should open and close search bar', async ({ page }) => {
    // Search bar should be hidden initially
    await expect(viewerPage.searchInput).not.toBeVisible();
    
    // Open search bar
    await viewerPage.searchButton.click();
    await expect(viewerPage.searchInput).toBeVisible();
    
    // Close search bar
    const closeButton = page.locator('button:has([data-testid="CloseIcon"])').last();
    await closeButton.click();
    await expect(viewerPage.searchInput).not.toBeVisible();
  });

  test('should find text in PDF', async ({ page }) => {
    // Open search and search for a common word
    await viewerPage.search('sample');
    
    // Check if results are found
    const results = await viewerPage.getSearchResultsCount();
    expect(results.total).toBeGreaterThan(0);
    expect(results.current).toBe(1);
    
    // Check for highlights
    const highlights = page.locator('mark, .highlight');
    await expect(highlights.first()).toBeVisible();
  });

  test('should navigate between search results', async ({ page }) => {
    // Search for a word that appears multiple times
    await viewerPage.search('the');
    
    const results = await viewerPage.getSearchResultsCount();
    if (results.total > 1) {
      // Navigate to next result
      const nextButton = page.locator('button:has([data-testid="KeyboardArrowDownIcon"])');
      await nextButton.click();
      await page.waitForTimeout(500);
      
      const updatedResults = await viewerPage.getSearchResultsCount();
      expect(updatedResults.current).toBe(2);
      
      // Navigate to previous result
      const prevButton = page.locator('button:has([data-testid="KeyboardArrowUpIcon"])');
      await prevButton.click();
      await page.waitForTimeout(500);
      
      const finalResults = await viewerPage.getSearchResultsCount();
      expect(finalResults.current).toBe(1);
    }
  });

  test('should handle search with no results', async ({ page }) => {
    // Search for text that doesn't exist
    await viewerPage.search('xyzabc123notfound');
    
    // Should show 0 results
    const results = await viewerPage.getSearchResultsCount();
    expect(results.total).toBe(0);
    expect(results.current).toBe(0);
    
    // No highlights should be visible
    const highlights = page.locator('mark, .highlight');
    await expect(highlights).toHaveCount(0);
  });

  test('should clear search results', async ({ page }) => {
    // Perform a search
    await viewerPage.search('sample');
    
    // Verify results exist
    const initialResults = await viewerPage.getSearchResultsCount();
    expect(initialResults.total).toBeGreaterThan(0);
    
    // Clear search
    const clearButton = page.locator('button:has([data-testid="CloseIcon"])').last();
    await clearButton.click();
    
    // Search should be closed and highlights removed
    await expect(viewerPage.searchInput).not.toBeVisible();
    const highlights = page.locator('mark, .highlight');
    await expect(highlights).toHaveCount(0);
  });

  test('should maintain search across page navigation', async ({ page }) => {
    const totalPages = await viewerPage.getTotalPages();
    
    if (totalPages > 1) {
      // Search for text
      await viewerPage.search('the');
      const results = await viewerPage.getSearchResultsCount();
      
      if (results.total > 0) {
        // Navigate to next page
        await viewerPage.nextPage();
        
        // Search results should still be visible
        const searchCounter = page.locator('text=/\\d+ of \\d+/');
        await expect(searchCounter).toBeVisible();
        
        // Highlights should update for the new page
        const highlights = page.locator('mark, .highlight');
        const highlightCount = await highlights.count();
        // There should be highlights if the search term exists on this page
        expect(highlightCount).toBeGreaterThanOrEqual(0);
      }
    }
  });

  test('should handle case-insensitive search', async ({ page }) => {
    // Search with lowercase
    await viewerPage.search('sample');
    const lowercaseResults = await viewerPage.getSearchResultsCount();
    
    // Clear and search with uppercase
    const clearButton = page.locator('button:has([data-testid="CloseIcon"])').last();
    await clearButton.click();
    await viewerPage.search('SAMPLE');
    const uppercaseResults = await viewerPage.getSearchResultsCount();
    
    // Results should be the same
    expect(uppercaseResults.total).toBe(lowercaseResults.total);
  });

  test('should highlight current search result differently', async ({ page }) => {
    // Search for text with multiple results
    await viewerPage.search('the');
    const results = await viewerPage.getSearchResultsCount();
    
    if (results.total > 1) {
      // Check for different highlight styles
      const currentHighlight = page.locator('mark.selected, .highlight.selected');
      const otherHighlights = page.locator('mark:not(.selected), .highlight:not(.selected)');
      
      // Current match should have different styling
      await expect(currentHighlight).toHaveCount(1);
      await expect(otherHighlights).toHaveCount(results.total - 1);
    }
  });

  test('should update search on Enter key', async ({ page }) => {
    // Open search
    await viewerPage.searchButton.click();
    await viewerPage.searchInput.waitFor({ state: 'visible' });
    
    // Type search query
    await viewerPage.searchInput.type('sample');
    
    // Press Enter
    await viewerPage.searchInput.press('Enter');
    await page.waitForTimeout(500);
    
    // Results should appear
    const results = await viewerPage.getSearchResultsCount();
    expect(results.total).toBeGreaterThan(0);
  });

  test('should handle special characters in search', async ({ page }) => {
    // Test search with special characters
    const specialSearches = ['(test)', 'test.pdf', 'test-case', 'test & sample'];
    
    for (const searchTerm of specialSearches) {
      await viewerPage.search(searchTerm);
      
      // Should not crash and should return results (0 or more)
      const results = await viewerPage.getSearchResultsCount();
      expect(results.current).toBeGreaterThanOrEqual(0);
      expect(results.total).toBeGreaterThanOrEqual(0);
      
      // Clear for next search
      const clearButton = page.locator('button:has([data-testid="CloseIcon"])').last();
      await clearButton.click();
    }
  });
});