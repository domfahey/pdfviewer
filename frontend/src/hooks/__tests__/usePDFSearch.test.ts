import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePDFSearch } from '../usePDFSearch';
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist';

// Mock PDF document and page objects
const createMockPage = (pageNum: number, textContent: string[]): PDFPageProxy =>
  ({
    pageNumber: pageNum,
    getTextContent: vi.fn().mockResolvedValue({
      items: textContent.map(text => ({ str: text })),
      styles: {},
    }),
    getViewport: vi.fn(),
    render: vi.fn(),
    getOperatorList: vi.fn(),
    streamTextContent: vi.fn(),
    getAnnotations: vi.fn(),
    cleanup: vi.fn(),
    stats: null,
    ref: { num: pageNum, gen: 0 },
    rotate: 0,
    view: [0, 0, 100, 100],
    userUnit: 1,
    getDisplayReadableText: vi.fn(),
    getStructTree: vi.fn(),
    transport: {} as object,
    objs: {} as object,
    commonObjs: {} as object,
    fontCache: {} as object,
    builtInCMapCache: {} as object,
    standardFontDataCache: {} as object,
    systemFontCache: {} as object,
    rendered: Promise.resolve(),
  }) as PDFPageProxy;

const createMockPDFDocument = (
  pages: Array<{ pageNum: number; textContent: string[] }>
): PDFDocumentProxy => {
  const pagesMap = new Map(pages.map(p => [p.pageNum, createMockPage(p.pageNum, p.textContent)]));

  return {
    numPages: pages.length,
    fingerprints: ['mock-fingerprint'],
    getPage: vi.fn().mockImplementation((pageNum: number) => {
      return Promise.resolve(pagesMap.get(pageNum));
    }),
    loadingTask: {} as object,
    getPageIndex: vi.fn(),
    getDestinations: vi.fn(),
    getDestination: vi.fn(),
    getPageLabels: vi.fn(),
    getPageLayout: vi.fn(),
    getPageMode: vi.fn(),
    getViewerPreferences: vi.fn(),
    getMetadata: vi.fn(),
    getMarkInfo: vi.fn(),
    getData: vi.fn(),
    saveDocument: vi.fn(),
    getDownloadInfo: vi.fn(),
    cleanup: vi.fn(),
    destroy: vi.fn(),
    cachedPageNumber: 1,
    loadingParams: {} as object,
    transport: {} as object,
    getDocumentId: vi.fn(),
    getOptionalContentConfig: vi.fn(),
    getPermissions: vi.fn(),
    getJSActions: vi.fn(),
    getFieldObjects: vi.fn(),
    hasJSActions: vi.fn(),
    getCalculationOrderIds: vi.fn(),
    getOutline: vi.fn(),
    getAttachments: vi.fn(),
    getJavaScript: vi.fn(),
    getPageLabel: vi.fn(),
    isPureXfa: false,
    allXfaHtml: false,
  } as PDFDocumentProxy;
};

describe('usePDFSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => usePDFSearch(null));

    expect(result.current.searchQuery).toBe('');
    expect(result.current.searchMatches).toEqual([]);
    expect(result.current.currentMatchIndex).toBe(-1);
    expect(result.current.isSearching).toBe(false);
    expect(result.current.totalMatches).toBe(0);
    expect(typeof result.current.search).toBe('function');
    expect(typeof result.current.nextMatch).toBe('function');
    expect(typeof result.current.previousMatch).toBe('function');
    expect(typeof result.current.clearSearch).toBe('function');
    expect(typeof result.current.getCurrentMatch).toBe('function');
  });

  describe('search functionality', () => {
    it('should handle search with no document', async () => {
      const { result } = renderHook(() => usePDFSearch(null));

      await act(async () => {
        await result.current.search('test');
      });

      expect(result.current.searchQuery).toBe('');
      expect(result.current.searchMatches).toEqual([]);
      expect(result.current.currentMatchIndex).toBe(-1);
      expect(result.current.isSearching).toBe(false);
    });

    it('should handle search with empty query', async () => {
      const mockDocument = createMockPDFDocument([{ pageNum: 1, textContent: ['Hello world'] }]);

      const { result } = renderHook(() => usePDFSearch(mockDocument));

      await act(async () => {
        await result.current.search('   '); // Whitespace only
      });

      expect(result.current.searchQuery).toBe('');
      expect(result.current.searchMatches).toEqual([]);
      expect(result.current.currentMatchIndex).toBe(-1);
      expect(result.current.isSearching).toBe(false);
    });

    it('should find matches across multiple pages', async () => {
      const mockDocument = createMockPDFDocument([
        { pageNum: 1, textContent: ['Hello world', 'This is a test document'] },
        { pageNum: 2, textContent: ['More test content', 'Another page'] },
        { pageNum: 3, textContent: ['Final test here', 'End of document'] },
      ]);

      const { result } = renderHook(() => usePDFSearch(mockDocument));

      await act(async () => {
        await result.current.search('test');
      });

      expect(result.current.searchQuery).toBe('test');
      expect(result.current.searchMatches).toHaveLength(3);
      expect(result.current.currentMatchIndex).toBe(0);
      expect(result.current.isSearching).toBe(false);
      expect(result.current.totalMatches).toBe(3);

      // Check match details
      expect(result.current.searchMatches[0]).toEqual({
        pageIndex: 0, // 0-based
        matchIndex: 0,
        text: 'test',
      });
      expect(result.current.searchMatches[1]).toEqual({
        pageIndex: 1,
        matchIndex: 1,
        text: 'test',
      });
      expect(result.current.searchMatches[2]).toEqual({
        pageIndex: 2,
        matchIndex: 2,
        text: 'test',
      });
    });

    it('should handle case-insensitive search', async () => {
      const mockDocument = createMockPDFDocument([
        { pageNum: 1, textContent: ['Hello WORLD', 'This is a Test document'] },
      ]);

      const { result } = renderHook(() => usePDFSearch(mockDocument));

      await act(async () => {
        await result.current.search('test');
      });

      expect(result.current.searchMatches).toHaveLength(1);
      expect(result.current.searchMatches[0].text).toBe('Test'); // Original case preserved
    });

    it('should find multiple matches on the same page', async () => {
      const mockDocument = createMockPDFDocument([
        { pageNum: 1, textContent: ['test document with test content and another test'] },
      ]);

      const { result } = renderHook(() => usePDFSearch(mockDocument));

      await act(async () => {
        await result.current.search('test');
      });

      expect(result.current.searchMatches).toHaveLength(3);
      expect(result.current.searchMatches.every(match => match.pageIndex === 0)).toBe(true);
      expect(result.current.searchMatches.map(match => match.matchIndex)).toEqual([0, 1, 2]);
    });

    it('should set searching state during search', async () => {
      const mockDocument = createMockPDFDocument([{ pageNum: 1, textContent: ['test content'] }]);

      const { result } = renderHook(() => usePDFSearch(mockDocument));

      // Start search but don't await
      act(() => {
        result.current.search('test');
      });

      // Check that searching state is set
      expect(result.current.isSearching).toBe(true);
      expect(result.current.searchQuery).toBe('test');

      // Wait for search to complete
      await waitFor(() => {
        expect(result.current.isSearching).toBe(false);
      });

      expect(result.current.searchMatches).toHaveLength(1);
    });

    it('should handle search cancellation', async () => {
      const mockDocument = createMockPDFDocument([
        { pageNum: 1, textContent: ['test content'] },
        { pageNum: 2, textContent: ['more content'] },
      ]);

      const { result } = renderHook(() => usePDFSearch(mockDocument));

      // Start first search
      act(() => {
        result.current.search('test');
      });

      // Immediately start second search (should cancel first)
      await act(async () => {
        await result.current.search('content');
      });

      expect(result.current.searchQuery).toBe('content');
      expect(result.current.searchMatches).toHaveLength(2);
    });

    it('should handle search errors gracefully', async () => {
      const mockDocument = createMockPDFDocument([{ pageNum: 1, textContent: ['test content'] }]);

      // Make getPage throw an error
      mockDocument.getPage = vi.fn().mockRejectedValue(new Error('Page load failed'));

      const { result } = renderHook(() => usePDFSearch(mockDocument));

      await act(async () => {
        await result.current.search('test');
      });

      expect(result.current.isSearching).toBe(false);
      expect(result.current.searchMatches).toEqual([]);
    });
  });

  describe('navigation functions', () => {
    let mockDocument: PDFDocumentProxy;

    beforeEach(async () => {
      mockDocument = createMockPDFDocument([
        { pageNum: 1, textContent: ['first test'] },
        { pageNum: 2, textContent: ['second test'] },
        { pageNum: 3, textContent: ['third test'] },
      ]);
    });

    it('should navigate to next match', async () => {
      const { result } = renderHook(() => usePDFSearch(mockDocument));

      await act(async () => {
        await result.current.search('test');
      });

      expect(result.current.currentMatchIndex).toBe(0);

      act(() => {
        result.current.nextMatch();
      });

      expect(result.current.currentMatchIndex).toBe(1);

      act(() => {
        result.current.nextMatch();
      });

      expect(result.current.currentMatchIndex).toBe(2);
    });

    it('should wrap around to first match when at end', async () => {
      const { result } = renderHook(() => usePDFSearch(mockDocument));

      await act(async () => {
        await result.current.search('test');
      });

      // Go to last match
      act(() => {
        result.current.nextMatch();
        result.current.nextMatch();
      });

      expect(result.current.currentMatchIndex).toBe(2);

      // Should wrap to first match
      act(() => {
        result.current.nextMatch();
      });

      expect(result.current.currentMatchIndex).toBe(0);
    });

    it('should navigate to previous match', async () => {
      const { result } = renderHook(() => usePDFSearch(mockDocument));

      await act(async () => {
        await result.current.search('test');
      });

      // Go to second match
      act(() => {
        result.current.nextMatch();
      });

      expect(result.current.currentMatchIndex).toBe(1);

      act(() => {
        result.current.previousMatch();
      });

      expect(result.current.currentMatchIndex).toBe(0);
    });

    it('should wrap around to last match when at beginning', async () => {
      const { result } = renderHook(() => usePDFSearch(mockDocument));

      await act(async () => {
        await result.current.search('test');
      });

      expect(result.current.currentMatchIndex).toBe(0);

      // Should wrap to last match
      act(() => {
        result.current.previousMatch();
      });

      expect(result.current.currentMatchIndex).toBe(2);
    });

    it('should handle navigation with no matches', () => {
      const { result } = renderHook(() => usePDFSearch(mockDocument));

      act(() => {
        result.current.nextMatch();
      });

      expect(result.current.currentMatchIndex).toBe(-1);

      act(() => {
        result.current.previousMatch();
      });

      expect(result.current.currentMatchIndex).toBe(-1);
    });
  });

  describe('getCurrentMatch', () => {
    it('should return current match when valid index', async () => {
      const mockDocument = createMockPDFDocument([
        { pageNum: 1, textContent: ['first test'] },
        { pageNum: 2, textContent: ['second test'] },
      ]);

      const { result } = renderHook(() => usePDFSearch(mockDocument));

      await act(async () => {
        await result.current.search('test');
      });

      const currentMatch = result.current.getCurrentMatch();
      expect(currentMatch).toEqual({
        pageIndex: 0,
        matchIndex: 0,
        text: 'test',
      });

      act(() => {
        result.current.nextMatch();
      });

      const nextMatch = result.current.getCurrentMatch();
      expect(nextMatch).toEqual({
        pageIndex: 1,
        matchIndex: 1,
        text: 'test',
      });
    });

    it('should return null when no matches', () => {
      const mockDocument = createMockPDFDocument([
        { pageNum: 1, textContent: ['no matches here'] },
      ]);

      const { result } = renderHook(() => usePDFSearch(mockDocument));

      const currentMatch = result.current.getCurrentMatch();
      expect(currentMatch).toBe(null);
    });

    it('should return null when invalid index', async () => {
      const mockDocument = createMockPDFDocument([{ pageNum: 1, textContent: ['test content'] }]);

      const { result } = renderHook(() => usePDFSearch(mockDocument));

      await act(async () => {
        await result.current.search('test');
      });

      // Manually corrupt the state for testing
      act(() => {
        // This simulates an edge case
        result.current.clearSearch();
      });

      const currentMatch = result.current.getCurrentMatch();
      expect(currentMatch).toBe(null);
    });
  });

  describe('clearSearch', () => {
    it('should clear search state', async () => {
      const mockDocument = createMockPDFDocument([{ pageNum: 1, textContent: ['test content'] }]);

      const { result } = renderHook(() => usePDFSearch(mockDocument));

      await act(async () => {
        await result.current.search('test');
      });

      expect(result.current.searchMatches).toHaveLength(1);
      expect(result.current.searchQuery).toBe('test');

      act(() => {
        result.current.clearSearch();
      });

      expect(result.current.searchQuery).toBe('');
      expect(result.current.searchMatches).toEqual([]);
      expect(result.current.currentMatchIndex).toBe(-1);
      expect(result.current.isSearching).toBe(false);
      expect(result.current.totalMatches).toBe(0);
    });

    it('should cancel ongoing search', async () => {
      const mockDocument = createMockPDFDocument([
        { pageNum: 1, textContent: ['test content'] },
        { pageNum: 2, textContent: ['more content'] },
      ]);

      const { result } = renderHook(() => usePDFSearch(mockDocument));

      // Start search
      act(() => {
        result.current.search('test');
      });

      expect(result.current.isSearching).toBe(true);

      // Clear search immediately
      act(() => {
        result.current.clearSearch();
      });

      expect(result.current.isSearching).toBe(false);
      expect(result.current.searchQuery).toBe('');
    });
  });

  describe('edge cases and error handling', () => {
    it('should handle document change during search', async () => {
      const firstDocument = createMockPDFDocument([{ pageNum: 1, textContent: ['first test'] }]);

      const { result, rerender } = renderHook(({ document }) => usePDFSearch(document), {
        initialProps: { document: firstDocument },
      });

      await act(async () => {
        await result.current.search('test');
      });

      expect(result.current.searchMatches).toHaveLength(1);

      // Change document
      const secondDocument = createMockPDFDocument([
        { pageNum: 1, textContent: ['second test', 'more test content'] },
      ]);

      rerender({ document: secondDocument });

      // Search again with new document
      await act(async () => {
        await result.current.search('test');
      });

      expect(result.current.searchMatches).toHaveLength(2);
    });

    it('should handle text content with special characters', async () => {
      const mockDocument = createMockPDFDocument([
        { pageNum: 1, textContent: ['Special chars: ñáéíóú test content'] },
      ]);

      const { result } = renderHook(() => usePDFSearch(mockDocument));

      await act(async () => {
        await result.current.search('test');
      });

      expect(result.current.searchMatches).toHaveLength(1);
      expect(result.current.searchMatches[0].text).toBe('test');
    });

    it('should handle overlapping matches correctly', async () => {
      const mockDocument = createMockPDFDocument([
        { pageNum: 1, textContent: ['aaaa'] }, // Multiple overlapping 'aa' matches
      ]);

      const { result } = renderHook(() => usePDFSearch(mockDocument));

      await act(async () => {
        await result.current.search('aa');
      });

      // Should find matches but not overlapping ones
      expect(result.current.searchMatches.length).toBeGreaterThan(0);
    });
  });
});
