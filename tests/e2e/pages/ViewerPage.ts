import { Page, Locator } from '@playwright/test';

export class ViewerPage {
  readonly page: Page;
  readonly pdfCanvas: Locator;
  readonly pageInput: Locator;
  readonly totalPagesText: Locator;
  readonly zoomSelect: Locator;
  readonly previousPageButton: Locator;
  readonly nextPageButton: Locator;
  readonly searchButton: Locator;
  readonly searchInput: Locator;
  readonly searchResults: Locator;
  readonly thumbnailsButton: Locator;
  readonly thumbnailsPanel: Locator;
  readonly fitWidthButton: Locator;
  readonly fitHeightButton: Locator;
  readonly fitPageButton: Locator;
  readonly rotateButton: Locator;
  readonly viewModeToggle: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pdfCanvas = page.locator('canvas').first();
    this.pageInput = page.locator('input[type="number"][value]').first();
    this.totalPagesText = page.locator('text=/of \\d+/');
    this.zoomSelect = page.locator('select:has-text("%")');
    this.previousPageButton = page.locator('button[aria-label="Previous page"]');
    this.nextPageButton = page.locator('button[aria-label="Next page"]');
    this.searchButton = page.locator('button:has([data-testid="SearchIcon"])');
    this.searchInput = page.locator('input[placeholder*="Search"]');
    this.searchResults = page.locator('text=/\\d+ of \\d+/');
    this.thumbnailsButton = page.locator('button:has([data-testid="ViewListIcon"])');
    this.thumbnailsPanel = page.locator('[data-testid="pdf-thumbnails"]');
    this.fitWidthButton = page.locator('button[aria-label="Fit to width"]');
    this.fitHeightButton = page.locator('button[aria-label="Fit to height"]');
    this.fitPageButton = page.locator('button[aria-label="Fit to page"]');
    this.rotateButton = page.locator('button:has([data-testid="RotateRightIcon"])');
    this.viewModeToggle = page.locator('[role="group"]:has-text("Original")');
  }

  async waitForPDFLoad() {
    await this.pdfCanvas.waitFor({ state: 'visible', timeout: 30000 });
    // Wait a bit more for the PDF to fully render
    await this.page.waitForTimeout(1000);
  }

  async getCurrentPage(): Promise<number> {
    const value = await this.pageInput.inputValue();
    return parseInt(value, 10);
  }

  async getTotalPages(): Promise<number> {
    const text = await this.totalPagesText.textContent();
    const match = text?.match(/of (\d+)/);
    return match ? parseInt(match[1], 10) : 0;
  }

  async goToPage(pageNumber: number) {
    await this.pageInput.fill(pageNumber.toString());
    await this.pageInput.press('Enter');
    await this.page.waitForTimeout(500); // Wait for page to load
  }

  async nextPage() {
    await this.nextPageButton.click();
    await this.page.waitForTimeout(500);
  }

  async previousPage() {
    await this.previousPageButton.click();
    await this.page.waitForTimeout(500);
  }

  async setZoom(zoomLevel: string) {
    await this.zoomSelect.selectOption(zoomLevel);
    await this.page.waitForTimeout(500);
  }

  async search(query: string) {
    await this.searchButton.click();
    await this.searchInput.waitFor({ state: 'visible' });
    await this.searchInput.fill(query);
    await this.searchInput.press('Enter');
    await this.page.waitForTimeout(1000); // Wait for search to complete
  }

  async getSearchResultsCount(): Promise<{ current: number; total: number }> {
    const text = await this.searchResults.textContent();
    const match = text?.match(/(\d+) of (\d+)/);
    if (match) {
      return {
        current: parseInt(match[1], 10),
        total: parseInt(match[2], 10),
      };
    }
    return { current: 0, total: 0 };
  }

  async toggleThumbnails() {
    await this.thumbnailsButton.click();
    await this.page.waitForTimeout(300);
  }

  async isThumbnailsPanelVisible(): Promise<boolean> {
    return await this.thumbnailsPanel.isVisible();
  }

  async selectThumbnail(pageNumber: number) {
    const thumbnail = this.page.locator(`[data-testid="thumbnail-${pageNumber}"]`);
    await thumbnail.click();
    await this.page.waitForTimeout(500);
  }

  async rotateDocument() {
    await this.rotateButton.click();
    await this.page.waitForTimeout(500);
  }

  async setFitMode(mode: 'width' | 'height' | 'page') {
    switch (mode) {
      case 'width':
        await this.fitWidthButton.click();
        break;
      case 'height':
        await this.fitHeightButton.click();
        break;
      case 'page':
        await this.fitPageButton.click();
        break;
    }
    await this.page.waitForTimeout(500);
  }

  async toggleViewMode() {
    const digitalButton = this.viewModeToggle.locator('button:has-text("Digital")');
    await digitalButton.click();
    await this.page.waitForTimeout(500);
  }

  async isPDFVisible(): Promise<boolean> {
    return await this.pdfCanvas.isVisible();
  }
}