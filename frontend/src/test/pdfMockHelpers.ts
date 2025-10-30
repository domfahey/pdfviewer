/**
 * Shared test utilities for creating PDF.js mock objects.
 *
 * This module provides reusable mock factories to reduce code duplication
 * across test files that work with PDF documents, pages, and text content.
 */

import { vi } from 'vitest';
import type { PDFDocumentProxy, PDFPageProxy, TextContent, TextItem } from 'pdfjs-dist';

/**
 * Create a mock TextContent object from a string.
 * Splits text by spaces to simulate individual text items.
 *
 * @param text - Text content to convert into TextContent
 * @returns Mock TextContent object
 */
export const createMockTextContent = (text: string): TextContent => ({
  items: text.split(' ').map(
    str =>
      ({
        str,
      }) as TextItem
  ),
  styles: {},
});

/**
 * Create a mock PDFPageProxy with specified content.
 *
 * @param pageNumber - Page number (1-indexed)
 * @param text - Text content for the page
 * @returns Mock PDFPageProxy object
 */
export const createMockPage = (pageNumber: number, text: string): PDFPageProxy =>
  ({
    pageNumber,
    getTextContent: vi.fn().mockResolvedValue(createMockTextContent(text)),
  }) as unknown as PDFPageProxy;

/**
 * Create a mock PDFDocumentProxy with multiple pages.
 *
 * @param pages - Array of page configurations with pageNum and text
 * @returns Mock PDFDocumentProxy object
 *
 * @example
 * const doc = createMockDocument([
 *   { pageNum: 1, text: 'hello world' },
 *   { pageNum: 2, text: 'goodbye world' }
 * ]);
 */
export const createMockDocument = (
  pages: Array<{ pageNum: number; text: string }>
): PDFDocumentProxy => {
  const mockPages = pages.map(p => createMockPage(p.pageNum, p.text));
  return {
    numPages: pages.length,
    getPage: vi
      .fn()
      .mockImplementation((pageNum: number) => Promise.resolve(mockPages[pageNum - 1])),
  } as unknown as PDFDocumentProxy;
};

/**
 * Create a mock text layer for PDF.js TextLayer.
 * Reduces duplication in text layer rendering tests.
 *
 * @returns Mock text layer with render function
 */
export const createMockTextLayer = () => ({
  render: vi.fn().mockResolvedValue(undefined),
});

/**
 * Perform a search operation and wait for results.
 * Reduces duplication in search test patterns.
 *
 * @param act - Testing library act function
 * @param waitFor - Testing library waitFor function
 * @param searchFn - Search function to call
 * @param query - Search query string
 * @param expectedMatches - Expected number of matches
 */
export const performSearchAndWait = async (
  act: (callback: () => Promise<void> | void) => Promise<void>,
  waitFor: (callback: () => void | Promise<void>) => Promise<void>,
  searchFn: (query: string) => Promise<void>,
  query: string,
  expectedMatches: number,
  resultGetter: () => { totalMatches: number; isSearching: boolean }
): Promise<void> => {
  await act(async () => {
    await searchFn(query);
  });

  await waitFor(() => {
    const result = resultGetter();
    expect(result.totalMatches).toBe(expectedMatches);
    expect(result.isSearching).toBe(false);
  });
};

/**
 * Load a document and wait for completion.
 * Reduces duplication in document loading test patterns.
 *
 * @param act - Testing library act function
 * @param waitFor - Testing library waitFor function
 * @param loadDocFn - Load document function to call
 * @param url - Document URL
 * @param expectedPages - Expected number of pages
 */
export const loadDocumentAndWait = async (
  act: (callback: () => Promise<void> | void) => Promise<void>,
  waitFor: (callback: () => void | Promise<void>) => Promise<void>,
  loadDocFn: (url: string) => Promise<void>,
  url: string,
  expectedPages: number,
  resultGetter: () => { totalPages: number }
): Promise<void> => {
  await act(async () => {
    await loadDocFn(url);
  });

  await waitFor(() => {
    expect(resultGetter().totalPages).toBe(expectedPages);
  });
};
