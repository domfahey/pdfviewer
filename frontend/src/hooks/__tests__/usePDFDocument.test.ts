/**
 * Comprehensive unit tests for usePDFDocument hook.
 * 
 * Tests cover document loading, page navigation, scaling,
 * error handling, and cleanup functionality.
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { usePDFDocument } from '../usePDFDocument';
import { PDFService } from '../../services/pdfService';
import type { PDFDocumentProxy } from 'pdfjs-dist';
import type { PDFMetadata } from '../../types/pdf.types';

// Mock PDFService
vi.mock('../../services/pdfService', () => ({
  PDFService: {
    loadDocument: vi.fn(),
    cleanup: vi.fn(),
  },
}));

describe('usePDFDocument', () => {
  const mockDocument: Partial<PDFDocumentProxy> = {
    numPages: 10,
    fingerprints: ['test-fingerprint'],
  };

  const mockMetadata: PDFMetadata = {
    page_count: 10,
    file_size: 1024000,
    title: 'Test Document',
    author: 'Test Author',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => usePDFDocument());

      expect(result.current.document).toBeNull();
      expect(result.current.currentPage).toBe(1);
      expect(result.current.totalPages).toBe(0);
      expect(result.current.scale).toBe(1.0);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.metadata).toBeNull();
    });

    it('should provide all required functions', () => {
      const { result } = renderHook(() => usePDFDocument());

      expect(typeof result.current.loadDocument).toBe('function');
      expect(typeof result.current.setCurrentPage).toBe('function');
      expect(typeof result.current.setScale).toBe('function');
      expect(typeof result.current.nextPage).toBe('function');
      expect(typeof result.current.previousPage).toBe('function');
      expect(typeof result.current.cleanup).toBe('function');
    });
  });

  describe('loadDocument', () => {
    it('should successfully load a document', async () => {
      vi.mocked(PDFService.loadDocument).mockResolvedValue(
        mockDocument as PDFDocumentProxy
      );

      const { result } = renderHook(() => usePDFDocument());

      await act(async () => {
        await result.current.loadDocument('test.pdf');
      });

      await waitFor(() => {
        expect(result.current.document).toBe(mockDocument);
        expect(result.current.totalPages).toBe(10);
        expect(result.current.currentPage).toBe(1);
        expect(result.current.loading).toBe(false);
        expect(result.current.error).toBeNull();
      });

      expect(PDFService.loadDocument).toHaveBeenCalledWith('test.pdf');
    });

    it('should set loading state during document load', async () => {
      vi.mocked(PDFService.loadDocument).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockDocument as PDFDocumentProxy), 100)
          )
      );

      const { result } = renderHook(() => usePDFDocument());

      act(() => {
        result.current.loadDocument('test.pdf');
      });

      expect(result.current.loading).toBe(true);

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });

    it('should load document with metadata', async () => {
      vi.mocked(PDFService.loadDocument).mockResolvedValue(
        mockDocument as PDFDocumentProxy
      );

      const { result } = renderHook(() => usePDFDocument());

      await act(async () => {
        await result.current.loadDocument('test.pdf', mockMetadata);
      });

      await waitFor(() => {
        expect(result.current.metadata).toEqual(mockMetadata);
      });
    });

    it('should handle document load failure', async () => {
      const errorMessage = 'Failed to load PDF';
      vi.mocked(PDFService.loadDocument).mockRejectedValue(
        new Error(errorMessage)
      );

      const { result } = renderHook(() => usePDFDocument());

      await act(async () => {
        await result.current.loadDocument('invalid.pdf');
      });

      await waitFor(() => {
        expect(result.current.error).toBe(errorMessage);
        expect(result.current.document).toBeNull();
        expect(result.current.totalPages).toBe(0);
        expect(result.current.loading).toBe(false);
      });
    });

    it('should reset error on new document load', async () => {
      vi.mocked(PDFService.loadDocument)
        .mockRejectedValueOnce(new Error('First error'))
        .mockResolvedValueOnce(mockDocument as PDFDocumentProxy);

      const { result } = renderHook(() => usePDFDocument());

      // First load fails
      await act(async () => {
        await result.current.loadDocument('fail.pdf');
      });

      await waitFor(() => {
        expect(result.current.error).toBe('First error');
      });

      // Second load succeeds
      await act(async () => {
        await result.current.loadDocument('success.pdf');
      });

      await waitFor(() => {
        expect(result.current.error).toBeNull();
        expect(result.current.document).toBe(mockDocument);
      });
    });
  });

  describe('Page Navigation', () => {
    beforeEach(async () => {
      vi.mocked(PDFService.loadDocument).mockResolvedValue(
        mockDocument as PDFDocumentProxy
      );
    });

    it('should set current page within valid range', async () => {
      const { result } = renderHook(() => usePDFDocument());

      await act(async () => {
        await result.current.loadDocument('test.pdf');
      });

      await waitFor(() => {
        expect(result.current.totalPages).toBe(10);
      });

      act(() => {
        result.current.setCurrentPage(5);
      });

      expect(result.current.currentPage).toBe(5);
    });

    it('should not set page below minimum', async () => {
      const { result } = renderHook(() => usePDFDocument());

      await act(async () => {
        await result.current.loadDocument('test.pdf');
      });

      await waitFor(() => {
        expect(result.current.totalPages).toBe(10);
      });

      act(() => {
        result.current.setCurrentPage(0);
      });

      expect(result.current.currentPage).toBe(1);
    });

    it('should not set page above maximum', async () => {
      const { result } = renderHook(() => usePDFDocument());

      await act(async () => {
        await result.current.loadDocument('test.pdf');
      });

      await waitFor(() => {
        expect(result.current.totalPages).toBe(10);
      });

      act(() => {
        result.current.setCurrentPage(15);
      });

      expect(result.current.currentPage).toBe(1);
    });

    it('should go to next page', async () => {
      const { result } = renderHook(() => usePDFDocument());

      await act(async () => {
        await result.current.loadDocument('test.pdf');
      });

      await waitFor(() => {
        expect(result.current.totalPages).toBe(10);
      });

      act(() => {
        result.current.nextPage();
      });

      expect(result.current.currentPage).toBe(2);

      act(() => {
        result.current.nextPage();
      });

      expect(result.current.currentPage).toBe(3);
    });

    it('should go to previous page', async () => {
      const { result } = renderHook(() => usePDFDocument());

      await act(async () => {
        await result.current.loadDocument('test.pdf');
      });

      await waitFor(() => {
        expect(result.current.totalPages).toBe(10);
      });

      act(() => {
        result.current.setCurrentPage(5);
      });

      act(() => {
        result.current.previousPage();
      });

      expect(result.current.currentPage).toBe(4);
    });

    it('should not go beyond first page when going previous', async () => {
      const { result } = renderHook(() => usePDFDocument());

      await act(async () => {
        await result.current.loadDocument('test.pdf');
      });

      await waitFor(() => {
        expect(result.current.currentPage).toBe(1);
      });

      act(() => {
        result.current.previousPage();
      });

      expect(result.current.currentPage).toBe(1);
    });

    it('should not go beyond last page when going next', async () => {
      const { result } = renderHook(() => usePDFDocument());

      await act(async () => {
        await result.current.loadDocument('test.pdf');
      });

      await waitFor(() => {
        expect(result.current.totalPages).toBe(10);
      });

      act(() => {
        result.current.setCurrentPage(10);
      });

      act(() => {
        result.current.nextPage();
      });

      expect(result.current.currentPage).toBe(10);
    });
  });

  describe('Scale Management', () => {
    it('should set scale within valid range', () => {
      const { result } = renderHook(() => usePDFDocument());

      act(() => {
        result.current.setScale(1.5);
      });

      expect(result.current.scale).toBe(1.5);
    });

    it('should not set scale below minimum', () => {
      const { result } = renderHook(() => usePDFDocument());

      act(() => {
        result.current.setScale(0.05);
      });

      expect(result.current.scale).toBe(1.0); // Should remain at initial value
    });

    it('should not set scale above maximum', () => {
      const { result } = renderHook(() => usePDFDocument());

      act(() => {
        result.current.setScale(10.0);
      });

      expect(result.current.scale).toBe(1.0); // Should remain at initial value
    });

    it('should accept maximum valid scale', () => {
      const { result } = renderHook(() => usePDFDocument());

      act(() => {
        result.current.setScale(5.0);
      });

      expect(result.current.scale).toBe(5.0);
    });

    it('should accept minimum valid scale', () => {
      const { result } = renderHook(() => usePDFDocument());

      act(() => {
        result.current.setScale(0.2);
      });

      expect(result.current.scale).toBe(0.2);
    });
  });

  describe('Cleanup', () => {
    it('should cleanup document and reset state', async () => {
      vi.mocked(PDFService.loadDocument).mockResolvedValue(
        mockDocument as PDFDocumentProxy
      );

      const { result } = renderHook(() => usePDFDocument());

      await act(async () => {
        await result.current.loadDocument('test.pdf', mockMetadata);
      });

      await waitFor(() => {
        expect(result.current.document).toBe(mockDocument);
      });

      act(() => {
        result.current.cleanup();
      });

      expect(result.current.document).toBeNull();
      expect(result.current.currentPage).toBe(1);
      expect(result.current.totalPages).toBe(0);
      expect(result.current.metadata).toBeNull();
      expect(result.current.error).toBeNull();
      expect(PDFService.cleanup).toHaveBeenCalledWith(mockDocument);
    });

    it('should cleanup on unmount', async () => {
      vi.mocked(PDFService.loadDocument).mockResolvedValue(
        mockDocument as PDFDocumentProxy
      );

      const { result, unmount } = renderHook(() => usePDFDocument());

      await act(async () => {
        await result.current.loadDocument('test.pdf');
      });

      await waitFor(() => {
        expect(result.current.document).toBe(mockDocument);
      });

      unmount();

      expect(PDFService.cleanup).toHaveBeenCalledWith(mockDocument);
    });

    it('should handle cleanup when no document loaded', () => {
      const { result } = renderHook(() => usePDFDocument());

      act(() => {
        result.current.cleanup();
      });

      expect(PDFService.cleanup).not.toHaveBeenCalled();
      expect(result.current.document).toBeNull();
    });
  });

  describe('Edge Cases', () => {
    it('should handle concurrent document loads', async () => {
      const firstDoc = { ...mockDocument, numPages: 5 };
      const secondDoc = { ...mockDocument, numPages: 15 };

      vi.mocked(PDFService.loadDocument)
        .mockResolvedValueOnce(firstDoc as PDFDocumentProxy)
        .mockResolvedValueOnce(secondDoc as PDFDocumentProxy);

      const { result } = renderHook(() => usePDFDocument());

      await act(async () => {
        // Start both loads without awaiting the first
        const promise1 = result.current.loadDocument('first.pdf');
        const promise2 = result.current.loadDocument('second.pdf');
        await Promise.all([promise1, promise2]);
      });

      // Second document should be loaded
      await waitFor(() => {
        expect(result.current.totalPages).toBe(15);
      });
    });

    it('should handle empty URL gracefully', async () => {
      vi.mocked(PDFService.loadDocument).mockRejectedValue(
        new Error('Invalid URL')
      );

      const { result } = renderHook(() => usePDFDocument());

      await act(async () => {
        await result.current.loadDocument('');
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });
    });
  });
});
