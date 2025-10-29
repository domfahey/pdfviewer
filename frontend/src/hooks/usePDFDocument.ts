import { useState, useEffect, useCallback } from 'react';
import type { PDFDocumentProxy } from 'pdfjs-dist';
import { PDFService } from '../services/pdfService';
import type { PDFMetadata } from '../types/pdf.types';
import { devLog, devError } from '../utils/devLogger';

interface UsePDFDocumentReturn {
  document: PDFDocumentProxy | null;
  currentPage: number;
  totalPages: number;
  scale: number;
  loading: boolean;
  error: string | null;
  metadata: PDFMetadata | null;
  loadDocument: (url: string, metadata?: PDFMetadata) => Promise<void>;
  setCurrentPage: (page: number) => void;
  setScale: (scale: number) => void;
  nextPage: () => void;
  previousPage: () => void;
  cleanup: () => void;
}

/**
 * Custom hook for managing PDF document state and operations.
 * Provides document loading, page navigation, scaling, and metadata management.
 *
 * @returns Object containing document state and control functions
 */
export const usePDFDocument = (): UsePDFDocumentReturn => {
  const [document, setDocument] = useState<PDFDocumentProxy | null>(null);
  const [currentPage, setCurrentPageState] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [scale, setScaleState] = useState(1.0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<PDFMetadata | null>(null);

  const loadDocument = useCallback(async (url: string, docMetadata?: PDFMetadata) => {
    devLog('📖 [usePDFDocument] Starting document load:', {
      url,
      metadata: docMetadata,
      timestamp: new Date().toISOString(),
    });

    setLoading(true);
    setError(null);

    try {
      devLog('📚 [usePDFDocument] Calling PDFService.loadDocument...');
      const pdfDocument = await PDFService.loadDocument(url);

      devLog('✅ [usePDFDocument] Document loaded successfully:', {
        numPages: pdfDocument.numPages,
        fingerprint: pdfDocument.fingerprints?.[0] || 'unknown',
      });

      setDocument(pdfDocument);
      setTotalPages(pdfDocument.numPages);
      setCurrentPageState(1);

      if (docMetadata) {
        setMetadata(docMetadata);
      }
    } catch (error) {
      devError('❌ [usePDFDocument] Document load failed:', {
        error: error,
        message: error instanceof Error ? error.message : 'Failed to load document',
        url,
      });
      setError(error instanceof Error ? error.message : 'Failed to load document');
      setDocument(null);
      setTotalPages(0);
    } finally {
      setLoading(false);
    }
  }, []);

  const setCurrentPage = useCallback(
    (page: number) => {
      if (page >= 1 && page <= totalPages) {
        setCurrentPageState(page);
      }
    },
    [totalPages]
  );

  const setScale = useCallback((newScale: number) => {
    if (newScale > 0.1 && newScale <= 5.0) {
      setScaleState(newScale);
    }
  }, []);

  const nextPage = useCallback(() => {
    setCurrentPage(currentPage + 1);
  }, [currentPage, setCurrentPage]);

  const previousPage = useCallback(() => {
    setCurrentPage(currentPage - 1);
  }, [currentPage, setCurrentPage]);

  const cleanup = useCallback(() => {
    if (document) {
      PDFService.cleanup(document);
    }
    setDocument(null);
    setCurrentPageState(1);
    setTotalPages(0);
    setMetadata(null);
    setError(null);
  }, [document]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      devLog('🧹 [usePDFDocument] Hook unmounting, cleaning up document');
      if (document) {
        PDFService.cleanup(document);
      }
    };
  }, [document]); // Include document dependency for cleanup

  return {
    document,
    currentPage,
    totalPages,
    scale,
    loading,
    error,
    metadata,
    loadDocument,
    setCurrentPage,
    setScale,
    nextPage,
    previousPage,
    cleanup,
  };
};
