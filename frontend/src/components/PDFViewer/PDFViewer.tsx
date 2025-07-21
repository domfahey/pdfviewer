import React, { useState, useEffect, useCallback } from 'react';
import type { PDFPageProxy } from 'pdfjs-dist';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  AlertTitle,
  IconButton,
  Chip,
  Skeleton,
} from '@mui/material';
import { Error as ErrorIcon, Info as InfoIcon } from '@mui/icons-material';
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
        timestamp: new Date().toISOString(),
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
        documentExists: !!document,
      });

      setPageLoading(true);
      setPageError(null);

      try {
        const page = await PDFService.getPage(document, currentPage);
        console.log('✅ [PDFViewer] Page loaded successfully:', {
          pageNumber: page.pageNumber,
          pageExists: !!page,
        });
        setCurrentPageObj(page);
      } catch (err) {
        console.error('❌ [PDFViewer] Failed to load page:', {
          currentPage,
          error: err,
          message: err instanceof Error ? err.message : 'Failed to load page',
        });
        setPageError(err instanceof Error ? err.message : 'Failed to load page');
        setCurrentPageObj(null);
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
      // Account for thumbnails panel width when visible
      const thumbnailsWidth = showThumbnails ? 300 : 0;
      const metadataWidth = showMetadata ? 300 : 0;
      const containerWidth = window.innerWidth - thumbnailsWidth - metadataWidth - 40; // 40px for padding
      const containerHeight = window.innerHeight - 200; // Account for header and controls

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
    [showThumbnails, showMetadata]
  );

  // Recalculate fit mode when page loads or window resizes
  useEffect(() => {
    if (currentPageObj && fitMode.mode !== 'custom') {
      const newScale = calculateFitScale(
        fitMode.mode as 'width' | 'height' | 'page',
        currentPageObj
      );
      setScale(newScale);
    }
  }, [currentPageObj, fitMode.mode, calculateFitScale, setScale]);

  // Recalculate fit mode when panels are toggled
  useEffect(() => {
    if (currentPageObj && fitMode.mode !== 'custom') {
      const newScale = calculateFitScale(
        fitMode.mode as 'width' | 'height' | 'page',
        currentPageObj
      );
      setScale(newScale);
    }
  }, [showThumbnails, showMetadata, currentPageObj, fitMode.mode, calculateFitScale, setScale]);

  // Handle window resize for fit modes
  useEffect(() => {
    const handleResize = () => {
      if (currentPageObj && fitMode.mode !== 'custom') {
        const newScale = calculateFitScale(
          fitMode.mode as 'width' | 'height' | 'page',
          currentPageObj
        );
        setScale(newScale);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [currentPageObj, fitMode.mode, calculateFitScale, setScale]);

  const handleFitModeChange = useCallback(
    (newFitMode: FitMode) => {
      setFitMode(newFitMode);

      if (newFitMode.mode === 'custom' && newFitMode.scale) {
        setScale(newFitMode.scale);
      } else if (['width', 'height', 'page'].includes(newFitMode.mode)) {
        const newScale = calculateFitScale(
          newFitMode.mode as 'width' | 'height' | 'page',
          currentPageObj
        );
        setScale(newScale);
      }
    },
    [setScale, calculateFitScale, currentPageObj]
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

  if (!document || !currentPageObj) {
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
        <Alert severity="info" icon={<InfoIcon />}>
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

      {/* Main Content Area with Material Layout */}
      <Box sx={{ display: 'flex', flex: 1 }}>
        {/* Material Thumbnails Panel */}
        <PDFThumbnails
          pdfDocument={document}
          currentPage={currentPage}
          onPageSelect={setCurrentPage}
          isVisible={showThumbnails}
        />

        {/* Material Document Viewer */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Material Document Info Bar */}
          {metadata && (
            <Paper
              elevation={0}
              sx={{
                px: 3,
                py: 2,
                borderBottom: 1,
                borderColor: 'divider',
                bgcolor: 'background.paper',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {metadata.title || 'Untitled Document'}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip label={`${metadata.page_count} pages`} size="small" variant="outlined" />
                    <Chip
                      label={`${(metadata.file_size / (1024 * 1024)).toFixed(1)} MB`}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                  <IconButton onClick={handleToggleMetadata} size="small" color="primary">
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Box>
              </Box>
            </Paper>
          )}

          {/* Material Page Content Area */}
          <Box sx={{ flex: 1 }}>
            {useVirtualScrolling && document ? (
              <VirtualPDFViewer
                pdfDocument={document}
                scale={scale}
                currentPage={currentPage}
                onPageChange={setCurrentPage}
                className="h-full"
              />
            ) : (
              <Box sx={{ p: 3, minHeight: 'calc(100vh - 200px)' }}>
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
                  ) : currentPageObj ? (
                    <Box
                      sx={{
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
      </Box>
    </Box>
  );
};
