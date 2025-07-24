import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePDFDocument } from '../usePDFDocument';
import { PDFService } from '../../services/pdfService';
import type { PDFDocumentProxy } from 'pdfjs-dist';
import type { PDFMetadata } from '../../types/pdf.types';

// Mock the PDFService
vi.mock('../../services/pdfService', () => ({
  PDFService: {
    loadDocument: vi.fn(),
    cleanup: vi.fn(),
  },
}));

const mockPDFService = vi.mocked(PDFService);

// Mock PDF document
const createMockPDFDocument = (numPages: number = 5): PDFDocumentProxy =>
  ({
    numPages,
    fingerprints: ['mock-fingerprint'],
    loadingTask: {} as object,
    getPage: vi.fn(),
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
  }) as PDFDocumentProxy;

describe('usePDFDocument', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => usePDFDocument());

    expect(result.current.document).toBe(null);
    expect(result.current.currentPage).toBe(1);
    expect(result.current.totalPages).toBe(0);
    expect(result.current.scale).toBe(1.0);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.metadata).toBe(null);
    expect(typeof result.current.loadDocument).toBe('function');
    expect(typeof result.current.setCurrentPage).toBe('function');
    expect(typeof result.current.setScale).toBe('function');
    expect(typeof result.current.nextPage).toBe('function');
    expect(typeof result.current.previousPage).toBe('function');
    expect(typeof result.current.cleanup).toBe('function');
  });

  describe('loadDocument', () => {
    it('should successfully load a document', async () => {
      const { result } = renderHook(() => usePDFDocument());

      const mockDocument = createMockPDFDocument(10);
      mockPDFService.loadDocument.mockResolvedValue(mockDocument);

      const testUrl = 'http://example.com/test.pdf';
      const testMetadata: PDFMetadata = {
        title: 'Test Document',
        page_count: 10,
        file_size: 1024000,
        encrypted: false,
      };

      await act(async () => {
        await result.current.loadDocument(testUrl, testMetadata);
      });

      expect(mockPDFService.loadDocument).toHaveBeenCalledWith(testUrl);
      expect(result.current.document).toBe(mockDocument);
      expect(result.current.totalPages).toBe(10);
      expect(result.current.currentPage).toBe(1);
      expect(result.current.metadata).toBe(testMetadata);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe(null);
    });

    it('should handle loading without metadata', async () => {
      const { result } = renderHook(() => usePDFDocument());

      const mockDocument = createMockPDFDocument(5);
      mockPDFService.loadDocument.mockResolvedValue(mockDocument);

      const testUrl = 'http://example.com/test.pdf';

      await act(async () => {
        await result.current.loadDocument(testUrl);
      });

      expect(result.current.document).toBe(mockDocument);
      expect(result.current.totalPages).toBe(5);
      expect(result.current.metadata).toBe(null);
    });

    it('should set loading state during document load', async () => {
      const { result } = renderHook(() => usePDFDocument());

      const mockDocument = createMockPDFDocument(5);
      let resolveLoad: (value: PDFDocumentProxy) => void;

      mockPDFService.loadDocument.mockReturnValue(
        new Promise<PDFDocumentProxy>(resolve => {
          resolveLoad = resolve;
        })
      );

      const testUrl = 'http://example.com/test.pdf';

      act(() => {
        result.current.loadDocument(testUrl);
      });

      // Check loading state is set
      expect(result.current.loading).toBe(true);
      expect(result.current.error).toBe(null);

      // Resolve the promise
      await act(async () => {
        resolveLoad!(mockDocument);
      });

      expect(result.current.loading).toBe(false);
      expect(result.current.document).toBe(mockDocument);
    });

    it('should handle loading errors', async () => {
      const { result } = renderHook(() => usePDFDocument());

      const errorMessage = 'Failed to load PDF document';
      mockPDFService.loadDocument.mockRejectedValue(new Error(errorMessage));

      const testUrl = 'http://example.com/test.pdf';

      await act(async () => {
        await result.current.loadDocument(testUrl);
      });

      expect(result.current.error).toBe(errorMessage);
      expect(result.current.document).toBe(null);
      expect(result.current.totalPages).toBe(0);
      expect(result.current.loading).toBe(false);
    });

    it('should handle non-Error exceptions', async () => {
      const { result } = renderHook(() => usePDFDocument());

      mockPDFService.loadDocument.mockRejectedValue('String error');

      const testUrl = 'http://example.com/test.pdf';

      await act(async () => {
        await result.current.loadDocument(testUrl);
      });

      expect(result.current.error).toBe('Failed to load document');
      expect(result.current.document).toBe(null);
    });
  });

  describe('setCurrentPage', () => {
    it('should set current page within valid range', async () => {
      const { result } = renderHook(() => usePDFDocument());

      // First load a document
      const mockDocument = createMockPDFDocument(10);
      mockPDFService.loadDocument.mockResolvedValue(mockDocument);

      await act(async () => {
        await result.current.loadDocument('http://example.com/test.pdf');
      });

      // Now test page navigation
      act(() => {
        result.current.setCurrentPage(5);
      });

      expect(result.current.currentPage).toBe(5);
    });

    it('should not set page below 1', async () => {
      const { result } = renderHook(() => usePDFDocument());

      const mockDocument = createMockPDFDocument(10);
      mockPDFService.loadDocument.mockResolvedValue(mockDocument);

      await act(async () => {
        await result.current.loadDocument('http://example.com/test.pdf');
      });

      act(() => {
        result.current.setCurrentPage(0);
      });

      expect(result.current.currentPage).toBe(1); // Should remain at default
    });

    it('should not set page above total pages', async () => {
      const { result } = renderHook(() => usePDFDocument());

      const mockDocument = createMockPDFDocument(5);
      mockPDFService.loadDocument.mockResolvedValue(mockDocument);

      await act(async () => {
        await result.current.loadDocument('http://example.com/test.pdf');
      });

      act(() => {
        result.current.setCurrentPage(10);
      });

      expect(result.current.currentPage).toBe(1); // Should remain at default
    });
  });

  describe('setScale', () => {
    it('should set scale within valid range', () => {
      const { result } = renderHook(() => usePDFDocument());

      act(() => {
        result.current.setScale(1.5);
      });

      expect(result.current.scale).toBe(1.5);
    });

    it('should not set scale below minimum (0.1)', () => {
      const { result } = renderHook(() => usePDFDocument());

      act(() => {
        result.current.setScale(0.05);
      });

      expect(result.current.scale).toBe(1.0); // Should remain at default
    });

    it('should not set scale above maximum (5.0)', () => {
      const { result } = renderHook(() => usePDFDocument());

      act(() => {
        result.current.setScale(6.0);
      });

      expect(result.current.scale).toBe(1.0); // Should remain at default
    });

    it('should accept scale at boundaries', () => {
      const { result } = renderHook(() => usePDFDocument());

      // The validation is > 0.1, so 0.1 exactly should not be accepted
      act(() => {
        result.current.setScale(0.1);
      });
      expect(result.current.scale).toBe(1.0); // Should remain at default

      // Test with a value just above 0.1
      act(() => {
        result.current.setScale(0.11);
      });
      expect(result.current.scale).toBe(0.11);

      act(() => {
        result.current.setScale(5.0);
      });
      expect(result.current.scale).toBe(5.0);
    });
  });

  describe('nextPage and previousPage', () => {
    beforeEach(async () => {
      // This setup will be used by multiple tests
    });

    it('should navigate to next page', async () => {
      const { result } = renderHook(() => usePDFDocument());

      const mockDocument = createMockPDFDocument(5);
      mockPDFService.loadDocument.mockResolvedValue(mockDocument);

      await act(async () => {
        await result.current.loadDocument('http://example.com/test.pdf');
      });

      act(() => {
        result.current.nextPage();
      });

      expect(result.current.currentPage).toBe(2);
    });

    it('should navigate to previous page', async () => {
      const { result } = renderHook(() => usePDFDocument());

      const mockDocument = createMockPDFDocument(5);
      mockPDFService.loadDocument.mockResolvedValue(mockDocument);

      await act(async () => {
        await result.current.loadDocument('http://example.com/test.pdf');
      });

      // First go to page 3
      act(() => {
        result.current.setCurrentPage(3);
      });

      act(() => {
        result.current.previousPage();
      });

      expect(result.current.currentPage).toBe(2);
    });

    it('should not go beyond last page with nextPage', async () => {
      const { result } = renderHook(() => usePDFDocument());

      const mockDocument = createMockPDFDocument(3);
      mockPDFService.loadDocument.mockResolvedValue(mockDocument);

      await act(async () => {
        await result.current.loadDocument('http://example.com/test.pdf');
      });

      // Go to last page
      act(() => {
        result.current.setCurrentPage(3);
      });

      // Try to go to next page
      act(() => {
        result.current.nextPage();
      });

      expect(result.current.currentPage).toBe(3); // Should remain at last page
    });

    it('should not go below first page with previousPage', async () => {
      const { result } = renderHook(() => usePDFDocument());

      const mockDocument = createMockPDFDocument(5);
      mockPDFService.loadDocument.mockResolvedValue(mockDocument);

      await act(async () => {
        await result.current.loadDocument('http://example.com/test.pdf');
      });

      // Already on page 1
      act(() => {
        result.current.previousPage();
      });

      expect(result.current.currentPage).toBe(1); // Should remain at first page
    });
  });

  describe('cleanup', () => {
    it('should cleanup document and reset state', async () => {
      const { result } = renderHook(() => usePDFDocument());

      const mockDocument = createMockPDFDocument(10);
      mockPDFService.loadDocument.mockResolvedValue(mockDocument);

      const testMetadata: PDFMetadata = {
        title: 'Test Document',
        page_count: 10,
        file_size: 1024000,
        encrypted: false,
      };

      await act(async () => {
        await result.current.loadDocument('http://example.com/test.pdf', testMetadata);
      });

      // Verify document is loaded
      expect(result.current.document).toBe(mockDocument);
      expect(result.current.totalPages).toBe(10);
      expect(result.current.metadata).toBe(testMetadata);

      // Cleanup
      act(() => {
        result.current.cleanup();
      });

      expect(mockPDFService.cleanup).toHaveBeenCalledWith(mockDocument);
      expect(result.current.document).toBe(null);
      expect(result.current.currentPage).toBe(1);
      expect(result.current.totalPages).toBe(0);
      expect(result.current.metadata).toBe(null);
      expect(result.current.error).toBe(null);
    });

    it('should handle cleanup when no document is loaded', () => {
      const { result } = renderHook(() => usePDFDocument());

      act(() => {
        result.current.cleanup();
      });

      // Should not throw error and PDFService.cleanup should not be called
      expect(mockPDFService.cleanup).not.toHaveBeenCalled();
      expect(result.current.document).toBe(null);
    });
  });

  describe('hook lifecycle', () => {
    it('should cleanup document on unmount', async () => {
      const { result, unmount } = renderHook(() => usePDFDocument());

      const mockDocument = createMockPDFDocument(5);
      mockPDFService.loadDocument.mockResolvedValue(mockDocument);

      await act(async () => {
        await result.current.loadDocument('http://example.com/test.pdf');
      });

      expect(result.current.document).toBe(mockDocument);

      // Unmount the hook
      unmount();

      // Verify cleanup was called
      expect(mockPDFService.cleanup).toHaveBeenCalledWith(mockDocument);
    });

    it('should not cleanup if no document on unmount', () => {
      const { unmount } = renderHook(() => usePDFDocument());

      // Unmount without loading any document
      unmount();

      // Should not call cleanup
      expect(mockPDFService.cleanup).not.toHaveBeenCalled();
    });
  });

  describe('state consistency', () => {
    it('should maintain consistent state across multiple operations', async () => {
      const { result } = renderHook(() => usePDFDocument());

      const mockDocument = createMockPDFDocument(10);
      mockPDFService.loadDocument.mockResolvedValue(mockDocument);

      await act(async () => {
        await result.current.loadDocument('http://example.com/test.pdf');
      });

      // Perform multiple operations
      act(() => {
        result.current.setCurrentPage(5);
        result.current.setScale(1.5);
      });

      expect(result.current.currentPage).toBe(5);
      expect(result.current.scale).toBe(1.5);
      expect(result.current.totalPages).toBe(10);
      expect(result.current.document).toBe(mockDocument);

      // Navigate using helpers - start from page 5
      expect(result.current.currentPage).toBe(5);

      act(() => {
        result.current.nextPage();
      });
      expect(result.current.currentPage).toBe(6);

      act(() => {
        result.current.nextPage();
      });
      expect(result.current.currentPage).toBe(7);

      act(() => {
        result.current.previousPage();
      });

      expect(result.current.currentPage).toBe(6);
    });

    it('should reset state after loading error and successful reload', async () => {
      const { result } = renderHook(() => usePDFDocument());

      // First, cause an error
      mockPDFService.loadDocument.mockRejectedValue(new Error('Load failed'));

      await act(async () => {
        await result.current.loadDocument('http://example.com/bad.pdf');
      });

      expect(result.current.error).toBe('Load failed');
      expect(result.current.document).toBe(null);

      // Then load successfully
      const mockDocument = createMockPDFDocument(8);
      mockPDFService.loadDocument.mockResolvedValue(mockDocument);

      await act(async () => {
        await result.current.loadDocument('http://example.com/good.pdf');
      });

      expect(result.current.error).toBe(null);
      expect(result.current.document).toBe(mockDocument);
      expect(result.current.totalPages).toBe(8);
      expect(result.current.currentPage).toBe(1); // Reset to page 1
    });
  });
});
