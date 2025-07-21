import { Page, Locator } from '@playwright/test';

export class UploadPage {
  readonly page: Page;
  readonly dropZone: Locator;
  readonly fileInput: Locator;
  readonly uploadButton: Locator;
  readonly errorMessage: Locator;
  readonly successMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.dropZone = page.locator('[data-testid="pdf-drop-zone"], .MuiBox-root:has-text("Drop your PDF here")');
    this.fileInput = page.locator('input[type="file"]');
    this.uploadButton = page.locator('button:has-text("Upload")');
    this.errorMessage = page.locator('[role="alert"]:has-text("Error")');
    this.successMessage = page.locator('[role="alert"]:has-text("Success")');
  }

  async goto() {
    await this.page.goto('/');
  }

  async uploadFile(filePath: string) {
    // Set the file on the input element
    await this.fileInput.setInputFiles(filePath);
  }

  async dragAndDropFile(filePath: string) {
    // Create a data transfer object for drag and drop
    const buffer = await this.page.evaluateHandle(async (path) => {
      const response = await fetch(path);
      const data = await response.arrayBuffer();
      return data;
    }, filePath);

    // Simulate drag and drop
    await this.dropZone.dispatchEvent('drop', {
      dataTransfer: {
        files: [filePath],
      },
    });
  }

  async waitForUploadComplete() {
    // Wait for either success or navigation to viewer
    await Promise.race([
      this.page.waitForURL('**/viewer/**', { timeout: 30000 }),
      this.successMessage.waitFor({ state: 'visible', timeout: 30000 }),
    ]);
  }

  async getErrorMessage(): Promise<string | null> {
    if (await this.errorMessage.isVisible()) {
      return await this.errorMessage.textContent();
    }
    return null;
  }

  async isDropZoneVisible(): Promise<boolean> {
    return await this.dropZone.isVisible();
  }
}