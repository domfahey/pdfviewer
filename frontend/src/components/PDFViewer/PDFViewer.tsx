import React, { useState, useEffect, useCallback } from 'react';
import type { PDFPageProxy } from 'pdfjs-dist';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  AlertTitle,
  Skeleton,
} from '@mui/material';
import { Error as ErrorIcon, Article as ArticleIcon } from '@mui/icons-material';
import { usePDFDocument } from '../../hooks/usePDFDocument';
import { usePDFSearch } from '../../hooks/usePDFSearch';
import { PDFService } from '../../services/pdfService';
import { PDFPage } from './PDFPage';
import { PDFControls } from './PDFControls';
import { PDFThumbnails } from './PDFThumbnails';
import { VirtualPDFViewer } from './VirtualPDFViewer';
import { PDFMetadataPanel } from './PDFMetadataPanel';
import { PDFExtractedFields } from './PDFExtractedFields';
import type { PDFMetadata } from '../../types/pdf.types';
import { devLog, devError } from '../../utils/devLogger';

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

/**
 * Main PDF viewer component with comprehensive features.
 * Supports page navigation, zoom, search, thumbnails, metadata display,
 * and extracted field comparison. Can use virtual scrolling for performance.
 *
 * @param props - Component properties
 * @param props.fileUrl - URL of the PDF file to display
 * @param props.metadata - Optional PDF metadata for display
 * @param props.className - Optional CSS class name for styling
 * @param props.initialFitMode - Initial zoom/fit mode (default: fit to width)
 * @param props.useVirtualScrolling - Whether to use virtual scrolling for performance
 */
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

  const [currentPageProxy, setCurrentPageProxy] = useState<PDFPageProxy | null>(null);
  const [pageLoading, setPageLoading] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [fitMode, setFitMode] = useState<FitMode>(initialFitMode);
  const [viewMode, setViewMode] = useState<'original' | 'digital'>('original');
  const [showThumbnails, setShowThumbnails] = useState(false);
  const [thumbnailsWidth, setThumbnailsWidth] = useState(300);
  const [showMetadata, setShowMetadata] = useState(false);
  const [showExtractedFields, setShowExtractedFields] = useState(false);
  const [extractedFieldsWidth, setExtractedFieldsWidth] = useState(350);
  const [rotation, setRotation] = useState(0);

  // Search functionality
  const {
    searchQuery,
    currentMatchIndex,
    isSearching,
    totalMatches,
    search,
    nextMatch,
    previousMatch,
    clearSearch,
    getCurrentMatch,
  } = usePDFSearch(document);

  // Load the PDF document
  useEffect(() => {
    if (fileUrl) {
      devLog('📄 [PDFViewer] Loading document:', {
        fileUrl,
        metadata,
        timestamp: new Date().toISOString(),
      });
      loadDocument(fileUrl, metadata);
    } else {
      devLog('⚠️ [PDFViewer] No fileUrl provided');
    }
  }, [fileUrl, metadata, loadDocument]);

  // Load the current page
  useEffect(() => {
    const loadPage = async () => {
      if (!document) {
        devLog('⏭️ [PDFViewer] No document available for page loading');
        return;
      }

      devLog('📄 [PDFViewer] Loading page:', {
        currentPage,
        totalPages,
        documentExists: !!document,
      });

      setPageLoading(true);
      setPageError(null);

      try {
        const page = await PDFService.getPage(document, currentPage);
        devLog('✅ [PDFViewer] Page loaded successfully:', {
          pageNumber: page.pageNumber,
          pageExists: !!page,
        });
        setCurrentPageProxy(page);
      } catch (error) {
        devError('❌ [PDFViewer] Failed to load page:', {
          currentPage,
          error: error,
          message: error instanceof Error ? error.message : 'Failed to load page',
        });
        setPageError(error instanceof Error ? error.message : 'Failed to load page');
        setCurrentPageProxy(null);
      } finally {
        setPageLoading(false);
      }
    };

    loadPage();
  }, [document, currentPage, totalPages]);

  const handlePageRender = useCallback(() => {
    // Page rendered successfully
    setPageError(null);
  }, []);

  const handlePageError = useCallback((errorMessage: string) => {
    setPageError(errorMessage);
  }, []);

  const calculateFitScale = useCallback(
    (mode: 'width' | 'height' | 'page', pageObj: PDFPageProxy | null) => {
      if (!pageObj) return 1;

      // Get the PDF page's natural dimensions at scale 1
      const viewport = pageObj.getViewport({ scale: 1 });
      const pageWidth = viewport.width;
      const pageHeight = viewport.height;

      // Get the available container dimensions
      // Account for thumbnails, metadata, and extracted fields panel widths when visible
      const thumbnailsWidthActual = showThumbnails ? thumbnailsWidth : 0;
      const metadataWidth = showMetadata ? 300 : 0;
      const containerWidth = window.innerWidth - thumbnailsWidthActual - metadataWidth - 40; // 40px for padding
      const containerHeight = window.innerHeight - 120; // Account for PDF controls only

      let scale = 1;

      switch (mode) {
        case 'width':
          // Fit to container width with some padding
          scale = (containerWidth - 60) / pageWidth; // 60px for padding
          break;
        case 'height':
          // Fit to container height with some padding
          scale = (containerHeight - 60) / pageHeight; // 60px for padding
          break;
        case 'page': {
          // Fit to both width and height, using the smaller scale
          const widthScale = (containerWidth - 60) / pageWidth;
          const heightScale = (containerHeight - 60) / pageHeight;
          scale = Math.min(widthScale, heightScale);
          break;
        }
      }

      // Clamp scale to reasonable bounds
      return Math.max(0.1, Math.min(5.0, scale));
    },
    [showThumbnails, thumbnailsWidth, showMetadata]
  );

  // Recalculate fit mode when page loads or window resizes
  useEffect(() => {
    if (currentPageProxy && fitMode.mode !== 'custom') {
      const newScale = calculateFitScale(
        fitMode.mode as 'width' | 'height' | 'page',
        currentPageProxy
      );
      setScale(newScale);
    }
  }, [currentPageProxy, fitMode.mode, calculateFitScale, setScale]);

  // Recalculate fit mode when panels are toggled
  useEffect(() => {
    if (currentPageProxy && fitMode.mode !== 'custom') {
      const newScale = calculateFitScale(
        fitMode.mode as 'width' | 'height' | 'page',
        currentPageProxy
      );
      setScale(newScale);
    }
  }, [
    showThumbnails,
    thumbnailsWidth,
    showMetadata,
    currentPageProxy,
    fitMode.mode,
    calculateFitScale,
    setScale,
  ]);

  // Handle window resize for fit modes
  useEffect(() => {
    const handleResize = () => {
      if (currentPageProxy && fitMode.mode !== 'custom') {
        const newScale = calculateFitScale(
          fitMode.mode as 'width' | 'height' | 'page',
          currentPageProxy
        );
        setScale(newScale);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [currentPageProxy, fitMode.mode, calculateFitScale, setScale]);

  const handleFitModeChange = useCallback(
    (newFitMode: FitMode) => {
      setFitMode(newFitMode);

      if (newFitMode.mode === 'custom' && newFitMode.scale) {
        setScale(newFitMode.scale);
      } else if (['width', 'height', 'page'].includes(newFitMode.mode)) {
        const newScale = calculateFitScale(
          newFitMode.mode as 'width' | 'height' | 'page',
          currentPageProxy
        );
        setScale(newScale);
      }
    },
    [setScale, calculateFitScale, currentPageProxy]
  );

  const handleToggleThumbnails = useCallback(() => {
    setShowThumbnails(prev => !prev);
  }, []);

  const handleToggleMetadata = useCallback(() => {
    setShowMetadata(prev => !prev);
  }, []);

  const handleToggleExtractedFields = useCallback(() => {
    setShowExtractedFields(prev => !prev);
  }, []);

  const handleViewModeChange = useCallback((mode: 'original' | 'digital') => {
    setViewMode(mode);
  }, []);

  const handleThumbnailsResize = useCallback((width: number) => {
    setThumbnailsWidth(width);
  }, []);

  const handleSearch = useCallback(
    (query: string) => {
      devLog('🔍 [PDFViewer] Searching for:', query);
      search(query);
    },
    [search]
  );

  // Navigate to current search match
  useEffect(() => {
    const currentMatch = getCurrentMatch();
    if (currentMatch && document) {
      // Navigate to the page with the current match
      const targetPage = currentMatch.pageIndex + 1; // Convert back to 1-based
      if (targetPage !== currentPage) {
        devLog('🔍 [PDFViewer] Navigating to search result page:', targetPage);
        setCurrentPage(targetPage);
      }
    }
  }, [currentMatchIndex, getCurrentMatch, document, currentPage, setCurrentPage]);

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
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 256,
          bgcolor: 'background.default',
        }}
        className={className}
      >
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress size={48} sx={{ mb: 2 }} />
          <Typography variant="body1" color="text.secondary">
            Loading PDF...
          </Typography>
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 256,
          p: 3,
        }}
        className={className}
      >
        <Alert severity="error" sx={{ maxWidth: 400 }} icon={<ErrorIcon fontSize="large" />}>
          <AlertTitle sx={{ fontWeight: 600 }}>Failed to load PDF</AlertTitle>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Box>
    );
  }

  if (!document || !currentPageProxy) {
    return (
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 256,
          bgcolor: 'background.default',
        }}
        className={className}
      >
        <Alert severity="info">
          <Typography variant="body1">No PDF loaded</Typography>
        </Alert>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100%',
        bgcolor: 'background.default',
      }}
      className={className}
    >
      {/* Material PDF Controls */}
      <PDFControls
        currentPage={currentPage}
        totalPages={totalPages}
        scale={scale}
        fitMode={fitMode}
        viewMode={viewMode}
        onPageChange={setCurrentPage}
        onScaleChange={handleScaleChange}
        onFitModeChange={handleFitModeChange}
        onViewModeChange={handleViewModeChange}
        onPreviousPage={previousPage}
        onNextPage={nextPage}
        onToggleThumbnails={handleToggleThumbnails}
        onToggleBookmarks={handleToggleMetadata}
        onToggleExtractedFields={handleToggleExtractedFields}
        onSearch={handleSearch}
        onSearchNext={nextMatch}
        onSearchPrevious={previousMatch}
        onClearSearch={clearSearch}
        searchMatches={totalMatches}
        currentSearchMatch={currentMatchIndex}
        isSearching={isSearching}
        onRotate={handleRotate}
        showAdvanced={true}
      />

      {/* Main Content Area with Material Layout */}
      <Box sx={{ display: 'flex', flex: 1 }}>
        {/* Material Thumbnails Panel */}
        <PDFThumbnails
          pdfDocument={document}
          currentPage={currentPage}
          onPageSelect={setCurrentPage}
          isVisible={showThumbnails}
          width={thumbnailsWidth}
          onResize={handleThumbnailsResize}
        />

        {/* Material Document Viewer */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
          {/* Material Page Content Area */}
          <Box sx={{ flex: 1, overflow: 'auto' }}>
            {viewMode === 'original' ? (
              // Original PDF View
              useVirtualScrolling && document ? (
                <VirtualPDFViewer
                  pdfDocument={document}
                  scale={scale}
                  currentPage={currentPage}
                  onPageChange={setCurrentPage}
                  className="h-full"
                />
              ) : (
                <Box sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                    {pageLoading ? (
                      <Paper
                        elevation={2}
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          minHeight: 384,
                          width: '100%',
                          bgcolor: 'background.paper',
                        }}
                      >
                        <Box sx={{ textAlign: 'center' }}>
                          <CircularProgress size={32} sx={{ mb: 2 }} />
                          <Typography variant="body2" color="text.secondary">
                            Loading page {currentPage}...
                          </Typography>
                        </Box>
                      </Paper>
                    ) : pageError ? (
                      <Paper
                        elevation={2}
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          minHeight: 384,
                          width: '100%',
                          p: 3,
                        }}
                      >
                        <Alert severity="error" icon={<ErrorIcon />} sx={{ maxWidth: 400 }}>
                          <AlertTitle>Failed to load page</AlertTitle>
                          <Typography variant="body2">{pageError}</Typography>
                        </Alert>
                      </Paper>
                    ) : currentPageProxy ? (
                      <Box
                        sx={{
                          transform: `rotate(${rotation}deg)`,
                          transition: 'transform 0.3s ease',
                        }}
                      >
                        <PDFPage
                          page={currentPageProxy}
                          scale={scale}
                          searchQuery={searchQuery}
                          isCurrentSearchPage={getCurrentMatch()?.pageIndex === currentPage - 1}
                          onPageRender={handlePageRender}
                          onPageError={handlePageError}
                        />
                      </Box>
                    ) : (
                      <Skeleton
                        variant="rectangular"
                        width="100%"
                        height={400}
                        sx={{ borderRadius: 1 }}
                      />
                    )}
                  </Box>
                </Box>
              )
            ) : (
              // Digital Markdown View (Placeholder)
              <Box sx={{ p: 3 }}>
                <Paper
                  elevation={2}
                  sx={{
                    p: 4,
                    bgcolor: 'background.paper',
                    maxWidth: 800,
                    mx: 'auto',
                  }}
                >
                  <Box sx={{ textAlign: 'center', mb: 4 }}>
                    <ArticleIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
                    <Typography variant="h5" gutterBottom sx={{ fontWeight: 500 }}>
                      Digital View
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      Extracted markdown content will appear here
                    </Typography>
                  </Box>

                  <Box
                    sx={{
                      bgcolor: 'grey.50',
                      p: 3,
                      borderRadius: 1,
                      border: '1px dashed',
                      borderColor: 'grey.300',
                    }}
                  >
                    <Typography variant="h6" gutterBottom>
                      # Document Title
                    </Typography>
                    <Typography variant="body1" paragraph>
                      This is a placeholder for the extracted markdown content from the PDF. The
                      digital view will display structured, searchable text content extracted from
                      the original PDF document.
                    </Typography>
                    <Typography variant="body1" paragraph>
                      **Features coming soon:**
                    </Typography>
                    <Typography variant="body1" component="div">
                      - Full text extraction - Structured headings and sections - Tables and lists
                      formatting - Searchable content - Copy/paste functionality
                    </Typography>
                  </Box>
                </Paper>
              </Box>
            )}
          </Box>
        </Box>

        {/* Material Metadata Panel */}
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

        {/* Extracted Fields Panel */}
        <PDFExtractedFields
          isVisible={showExtractedFields}
          onClose={() => setShowExtractedFields(false)}
          width={extractedFieldsWidth}
          onResize={setExtractedFieldsWidth}
        />
      </Box>
    </Box>
  );
};
