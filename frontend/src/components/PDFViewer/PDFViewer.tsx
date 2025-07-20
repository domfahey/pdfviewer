import React, { useState, useEffect, useCallback } from 'react';
import type { PDFPageProxy } from 'pdfjs-dist';
import { usePDFDocument } from '../../hooks/usePDFDocument';
import { PDFService } from '../../services/pdfService';
import { PDFPage } from './PDFPage';
import { PDFControls } from './PDFControls';
import type { PDFMetadata } from '../../types/pdf.types';

interface PDFViewerProps {
  fileUrl: string;
  metadata?: PDFMetadata;
  className?: string;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({ fileUrl, metadata, className = '' }) => {
  const {
    document,
    currentPage,
    totalPages,
    scale,
    loading,
    error,
    loadDocument,
    setCurrentPage,
    setScale,
    nextPage,
    previousPage,
  } = usePDFDocument();

  const [currentPageObj, setCurrentPageObj] = useState<PDFPageProxy | null>(null);
  const [pageLoading, setPageLoading] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);

  // Load the PDF document
  useEffect(() => {
    if (fileUrl) {
      loadDocument(fileUrl, metadata);
    }
  }, [fileUrl, metadata, loadDocument]);

  // Load the current page
  useEffect(() => {
    const loadPage = async () => {
      if (!document) return;

      setPageLoading(true);
      setPageError(null);

      try {
        const page = await PDFService.getPage(document, currentPage);
        setCurrentPageObj(page);
      } catch (err) {
        setPageError(err instanceof Error ? err.message : 'Failed to load page');
        setCurrentPageObj(null);
      } finally {
        setPageLoading(false);
      }
    };

    loadPage();
  }, [document, currentPage]);

  const handlePageRender = useCallback(() => {
    // Page rendered successfully
    setPageError(null);
  }, []);

  const handlePageError = useCallback((errorMessage: string) => {
    setPageError(errorMessage);
  }, []);

  const handleKeyPress = useCallback(
    (event: KeyboardEvent) => {
      switch (event.key) {
        case 'ArrowLeft':
        case 'PageUp':
          if (currentPage > 1) {
            previousPage();
          }
          break;
        case 'ArrowRight':
        case 'PageDown':
        case ' ':
          if (currentPage < totalPages) {
            nextPage();
          }
          event.preventDefault(); // Prevent page scroll on spacebar
          break;
        case 'Home':
          setCurrentPage(1);
          break;
        case 'End':
          setCurrentPage(totalPages);
          break;
        case '+':
        case '=':
          setScale(Math.min(5.0, scale + 0.25));
          break;
        case '-':
          setScale(Math.max(0.25, scale - 0.25));
          break;
      }
    },
    [currentPage, totalPages, scale, previousPage, nextPage, setCurrentPage, setScale]
  );

  // Add keyboard event listeners
  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [handleKeyPress]);

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-gray-600">Loading PDF...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="text-center">
          <div className="text-red-600 mb-2">
            <svg
              className="w-12 h-12 mx-auto mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="text-gray-900 font-medium">Failed to load PDF</div>
          <div className="text-gray-600 text-sm mt-1">{error}</div>
        </div>
      </div>
    );
  }

  if (!document || !currentPageObj) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="text-center">
          <div className="text-gray-600">No PDF loaded</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full bg-gray-50 ${className}`}>
      {/* Controls */}
      <PDFControls
        currentPage={currentPage}
        totalPages={totalPages}
        scale={scale}
        onPageChange={setCurrentPage}
        onScaleChange={setScale}
        onPreviousPage={previousPage}
        onNextPage={nextPage}
      />

      {/* Document Info */}
      {metadata && (
        <div className="px-4 py-2 bg-white border-b text-sm text-gray-600">
          <div className="flex items-center justify-between">
            <span>{metadata.title || 'Untitled Document'}</span>
            <span>
              {metadata.page_count} pages • {(metadata.file_size / (1024 * 1024)).toFixed(1)} MB
            </span>
          </div>
        </div>
      )}

      {/* Page Content */}
      <div className="flex-1 overflow-auto p-4">
        <div className="flex justify-center">
          {pageLoading ? (
            <div className="flex items-center justify-center h-96 w-full bg-white rounded shadow">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                <div className="text-gray-600 text-sm">Loading page {currentPage}...</div>
              </div>
            </div>
          ) : pageError ? (
            <div className="flex items-center justify-center h-96 w-full bg-white rounded shadow">
              <div className="text-center">
                <div className="text-red-600 mb-2">
                  <svg
                    className="w-8 h-8 mx-auto mb-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <div className="text-gray-900 font-medium">Failed to load page</div>
                <div className="text-gray-600 text-sm mt-1">{pageError}</div>
              </div>
            </div>
          ) : (
            <PDFPage
              page={currentPageObj}
              scale={scale}
              onPageRender={handlePageRender}
              onPageError={handlePageError}
            />
          )}
        </div>
      </div>
    </div>
  );
};
