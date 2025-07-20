import React, { useState, useEffect, useCallback } from 'react';
import type { PDFPageProxy } from 'pdfjs-dist';
import { usePDFDocument } from '../../hooks/usePDFDocument';
import { PDFService } from '../../services/pdfService';
import { PDFPage } from './PDFPage';
import { PDFControls } from './PDFControls';
import { PDFThumbnails } from './PDFThumbnails';
import { VirtualPDFViewer } from './VirtualPDFViewer';
import { PDFMetadataPanel } from './PDFMetadataPanel';
import type { PDFMetadata } from '../../types/pdf.types';

interface FitMode {
  mode: 'width' | 'height' | 'page' | 'custom';
  scale?: number;
}

interface PDFViewerProps {
  fileUrl: string;
  metadata?: PDFMetadata;
  className?: string;
  initialFitMode?: FitMode;
  useVirtualScrolling?: boolean;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({
  fileUrl,
  metadata,
  className = '',
  initialFitMode = { mode: 'width' },
  useVirtualScrolling = false,
}) => {
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
  const [fitMode, setFitMode] = useState<FitMode>(initialFitMode);
  const [showThumbnails, setShowThumbnails] = useState(false);
  const [showMetadata, setShowMetadata] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [, setSearchQuery] = useState('');

  // Load the PDF document
  useEffect(() => {
    if (fileUrl) {
      console.log('📄 [PDFViewer] Loading document:', {
        fileUrl,
        metadata,
        timestamp: new Date().toISOString()
      });
      loadDocument(fileUrl, metadata);
    } else {
      console.log('⚠️ [PDFViewer] No fileUrl provided');
    }
  }, [fileUrl, metadata, loadDocument]);

  // Load the current page
  useEffect(() => {
    const loadPage = async () => {
      if (!document) {
        console.log('⏭️ [PDFViewer] No document available for page loading');
        return;
      }

      console.log('📄 [PDFViewer] Loading page:', {
        currentPage,
        totalPages,
        documentExists: !!document
      });

      setPageLoading(true);
      setPageError(null);

      try {
        const page = await PDFService.getPage(document, currentPage);
        console.log('✅ [PDFViewer] Page loaded successfully:', {
          pageNumber: page.pageNumber,
          pageExists: !!page
        });
        setCurrentPageObj(page);
      } catch (err) {
        console.error('❌ [PDFViewer] Failed to load page:', {
          currentPage,
          error: err,
          message: err instanceof Error ? err.message : 'Failed to load page'
        });
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

  const handleFitModeChange = useCallback(
    (newFitMode: FitMode) => {
      setFitMode(newFitMode);
      if (newFitMode.mode === 'custom' && newFitMode.scale) {
        setScale(newFitMode.scale);
      }
    },
    [setScale]
  );

  const handleToggleThumbnails = useCallback(() => {
    setShowThumbnails(prev => !prev);
  }, []);

  const handleToggleMetadata = useCallback(() => {
    setShowMetadata(prev => !prev);
  }, []);

  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
    // TODO: Implement search functionality
    console.log('Searching for:', query);
  }, []);

  const handleRotate = useCallback((degrees: number) => {
    setRotation(prev => (prev + degrees) % 360);
  }, []);

  const handleScaleChange = useCallback(
    (newScale: number) => {
      setScale(newScale);
      setFitMode({ mode: 'custom', scale: newScale });
    },
    [setScale]
  );

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
      {/* Enhanced Controls */}
      <PDFControls
        currentPage={currentPage}
        totalPages={totalPages}
        scale={scale}
        fitMode={fitMode}
        onPageChange={setCurrentPage}
        onScaleChange={handleScaleChange}
        onFitModeChange={handleFitModeChange}
        onPreviousPage={previousPage}
        onNextPage={nextPage}
        onToggleThumbnails={handleToggleThumbnails}
        onToggleBookmarks={handleToggleMetadata}
        onSearch={handleSearch}
        onRotate={handleRotate}
        showAdvanced={true}
      />

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Thumbnails Panel */}
        <PDFThumbnails
          pdfDocument={document}
          currentPage={currentPage}
          onPageSelect={setCurrentPage}
          isVisible={showThumbnails}
        />

        {/* Document Viewer */}
        <div className="flex-1 flex flex-col">
          {/* Document Info */}
          {metadata && (
            <div className="px-4 py-2 bg-white border-b text-sm text-gray-600">
              <div className="flex items-center justify-between">
                <span>{metadata.title || 'Untitled Document'}</span>
                <div className="flex items-center space-x-4">
                  <span>
                    {metadata.page_count} pages • {(metadata.file_size / (1024 * 1024)).toFixed(1)}{' '}
                    MB
                  </span>
                  <button
                    onClick={handleToggleMetadata}
                    className="text-blue-600 hover:text-blue-800 text-xs underline"
                  >
                    {showMetadata ? 'Hide' : 'Show'} Details
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Page Content */}
          <div className="flex-1 overflow-hidden">
            {useVirtualScrolling && document ? (
              <VirtualPDFViewer
                pdfDocument={document}
                scale={scale}
                currentPage={currentPage}
                onPageChange={setCurrentPage}
                className="h-full"
              />
            ) : (
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
                  ) : currentPageObj ? (
                    <div
                      style={{
                        transform: `rotate(${rotation}deg)`,
                        transition: 'transform 0.3s ease',
                      }}
                    >
                      <PDFPage
                        page={currentPageObj}
                        scale={scale}
                        onPageRender={handlePageRender}
                        onPageError={handlePageError}
                      />
                    </div>
                  ) : null}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Metadata Panel */}
        <PDFMetadataPanel
          pdfDocument={document}
          fileMetadata={
            metadata
              ? {
                  filename: metadata.title || 'document.pdf',
                  file_size: metadata.file_size,
                  upload_time: new Date().toISOString(),
                  mime_type: 'application/pdf',
                }
              : undefined
          }
          isVisible={showMetadata}
        />
      </div>
    </div>
  );
};
