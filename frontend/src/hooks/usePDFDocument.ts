import { useState, useEffect, useCallback } from 'react';
import type { PDFDocumentProxy } from 'pdfjs-dist';
import { PDFService } from '../services/pdfService';
import type { PDFMetadata } from '../types/pdf.types';

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

export const usePDFDocument = (): UsePDFDocumentReturn => {
  const [document, setDocument] = useState<PDFDocumentProxy | null>(null);
  const [currentPage, setCurrentPageState] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [scale, setScaleState] = useState(1.0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<PDFMetadata | null>(null);

  const loadDocument = useCallback(async (url: string, docMetadata?: PDFMetadata) => {
    console.log('📖 [usePDFDocument] Starting document load:', {
      url,
      metadata: docMetadata,
      timestamp: new Date().toISOString()
    });

    setLoading(true);
    setError(null);

    try {
      console.log('📚 [usePDFDocument] Calling PDFService.loadDocument...');
      const pdfDocument = await PDFService.loadDocument(url);
      
      console.log('✅ [usePDFDocument] Document loaded successfully:', {
        numPages: pdfDocument.numPages,
        fingerprint: pdfDocument.fingerprints?.[0] || 'unknown'
      });

      setDocument(pdfDocument);
      setTotalPages(pdfDocument.numPages);
      setCurrentPageState(1);

      if (docMetadata) {
        setMetadata(docMetadata);
      }
    } catch (err) {
      console.error('❌ [usePDFDocument] Document load failed:', {
        error: err,
        message: err instanceof Error ? err.message : 'Failed to load document',
        url
      });
      setError(err instanceof Error ? err.message : 'Failed to load document');
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
      console.log('🧹 [usePDFDocument] Hook unmounting, cleaning up document');
      if (document) {
        PDFService.cleanup(document);
      }
    };
  }, []); // Empty dependency array - only run on unmount

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
