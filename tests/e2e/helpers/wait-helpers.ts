import { Page, Response } from '@playwright/test';

/**
 * Helper functions for resilient waiting in tests
 */

export interface WaitForResponseOptions {
  timeout?: number;
  predicate?: (response: Response) => boolean;
}

/**
 * Wait for an API response with custom timeout and retry logic
 */
export async function waitForAPIResponse(
  page: Page,
  urlPattern: string | RegExp,
  options: WaitForResponseOptions = {}
): Promise<Response> {
  const { timeout = 30000, predicate } = options;
  
  return page.waitForResponse(
    (response) => {
      const matchesUrl = typeof urlPattern === 'string' 
        ? response.url().includes(urlPattern)
        : urlPattern.test(response.url());
        
      const matchesPredicate = predicate ? predicate(response) : true;
      
      return matchesUrl && matchesPredicate;
    },
    { timeout }
  );
}

/**
 * Wait for element to be ready for interaction
 */
export async function waitForElementReady(
  page: Page,
  selector: string,
  options: { timeout?: number } = {}
): Promise<void> {
  const { timeout = 15000 } = options;
  
  // Wait for element to be attached to DOM
  await page.waitForSelector(selector, { 
    state: 'attached', 
    timeout 
  });
  
  // Wait for element to be visible
  await page.waitForSelector(selector, { 
    state: 'visible', 
    timeout 
  });
  
  // Small delay to ensure element is interactive
  await page.waitForTimeout(100);
}

/**
 * Retry an action with exponential backoff
 */
export async function retryWithBackoff<T>(
  action: () => Promise<T>,
  options: {
    maxAttempts?: number;
    initialDelay?: number;
    maxDelay?: number;
    shouldRetry?: (error: any) => boolean;
  } = {}
): Promise<T> {
  const {
    maxAttempts = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    shouldRetry = () => true
  } = options;
  
  let lastError: any;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await action();
    } catch (error) {
      lastError = error;
      
      if (attempt === maxAttempts || !shouldRetry(error)) {
        throw error;
      }
      
      const delay = Math.min(initialDelay * Math.pow(2, attempt - 1), maxDelay);
      console.log(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
}

/**
 * Wait for PDF to be fully loaded in the viewer
 */
export async function waitForPDFLoad(
  page: Page,
  options: { timeout?: number } = {}
): Promise<void> {
  const { timeout = 30000 } = options;
  
  // Wait for PDF canvas to be rendered
  await page.waitForSelector('canvas.pdf-page-canvas', {
    state: 'visible',
    timeout
  });
  
  // Wait for at least one page to have content
  await page.waitForFunction(
    () => {
      const canvas = document.querySelector('canvas.pdf-page-canvas') as HTMLCanvasElement;
      if (!canvas) return false;
      
      // Check if canvas has been drawn to
      const ctx = canvas.getContext('2d');
      if (!ctx) return false;
      
      // Check canvas dimensions
      return canvas.width > 0 && canvas.height > 0;
    },
    { timeout }
  );
  
  // Additional wait for text layer if present
  try {
    await page.waitForSelector('.textLayer', { 
      state: 'visible', 
      timeout: 5000 
    });
  } catch {
    // Text layer might not be present for image-based PDFs
  }
}

/**
 * Wait for loading state to complete
 */
export async function waitForLoadingComplete(
  page: Page,
  options: { timeout?: number } = {}
): Promise<void> {
  const { timeout = 30000 } = options;
  
  // Wait for any loading indicators to disappear
  await page.waitForFunction(
    () => {
      // Check for common loading indicators
      const loadingSelectors = [
        '[role="progressbar"]',
        '.loading',
        '.spinner',
        '[data-loading="true"]'
      ];
      
      for (const selector of loadingSelectors) {
        const element = document.querySelector(selector);
        if (element && window.getComputedStyle(element).display !== 'none') {
          return false;
        }
      }
      
      return true;
    },
    { timeout }
  );
}

/**
 * Check if we're on the expected port
 */
export async function ensureCorrectPort(
  page: Page,
  expectedPort: number
): Promise<void> {
  const currentUrl = page.url();
  const url = new URL(currentUrl);
  
  if (url.port !== expectedPort.toString()) {
    const newUrl = `${url.protocol}//${url.hostname}:${expectedPort}${url.pathname}${url.search}${url.hash}`;
    await page.goto(newUrl);
  }
}