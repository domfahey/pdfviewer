import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import { renderPageToCanvas, canvasToDataURL, cleanupCanvas } from '../../utils/canvasRenderer';

interface VirtualPDFViewerProps {
  pdfDocument: pdfjsLib.PDFDocumentProxy | null;
  scale: number;
  currentPage: number;
  onPageChange: (page: number) => void;
  className?: string;
  showPageNumbers?: boolean;
}

interface PageRenderData {
  pageNumber: number;
  canvas: HTMLCanvasElement | null;
  dataUrl: string | null; // Cache toDataURL result
  isRendered: boolean;
  isVisible: boolean;
  height: number;
  width: number;
}

const VIEWPORT_OVERSCAN = 2; // Number of pages to render outside viewport
const DEFAULT_PAGE_HEIGHT = 800;
const DEFAULT_PAGE_WIDTH = 600;
const MEMORY_CLEANUP_DELAY = 2000; // Reduced from 5000ms to 2000ms

export const VirtualPDFViewer: React.FC<VirtualPDFViewerProps> = ({
  pdfDocument,
  scale,
  currentPage,
  onPageChange,
  className = '',
  showPageNumbers = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [pageData, setPageData] = useState<PageRenderData[]>([]);
  const [containerHeight, setContainerHeight] = useState(0);
  const [scrollTop, setScrollTop] = useState(0);
  const renderingPages = useRef<Set<number>>(new Set());

  // Initialize page data when document loads
  useEffect(() => {
    if (!pdfDocument) {
      setPageData([]);
      return;
    }

    const initializePages = async () => {
      const pages: PageRenderData[] = [];

      for (let i = 1; i <= pdfDocument.numPages; i++) {
        try {
          const page = await pdfDocument.getPage(i);
          const viewport = page.getViewport({ scale });

          pages.push({
            pageNumber: i,
            canvas: null,
            dataUrl: null,
            isRendered: false,
            isVisible: false,
            height: viewport.height,
            width: viewport.width,
          });
        } catch (error) {
          console.error(`Error loading page ${i}:`, error);
          pages.push({
            pageNumber: i,
            canvas: null,
            dataUrl: null,
            isRendered: false,
            isVisible: false,
            height: DEFAULT_PAGE_HEIGHT * scale,
            width: DEFAULT_PAGE_WIDTH * scale,
          });
        }
      }

      setPageData(pages);
    };

    initializePages();
  }, [pdfDocument, scale]);

  // Calculate which pages should be visible
  const visiblePages = useMemo(() => {
    if (!containerHeight || pageData.length === 0) return [];

    const visiblePageIndices: number[] = [];
    let currentY = 0;
    const viewportTop = scrollTop;
    const viewportBottom = scrollTop + containerHeight;

    for (let i = 0; i < pageData.length; i++) {
      const pageBottom = currentY + pageData[i].height + 20; // 20px margin

      // Check if page intersects with viewport (with overscan)
      if (
        pageBottom >= viewportTop - VIEWPORT_OVERSCAN * DEFAULT_PAGE_HEIGHT * scale &&
        currentY <= viewportBottom + VIEWPORT_OVERSCAN * DEFAULT_PAGE_HEIGHT * scale
      ) {
        visiblePageIndices.push(i);
      }

      currentY = pageBottom;
    }

    return visiblePageIndices;
  }, [pageData, containerHeight, scrollTop, scale]);

  // Render pages that should be visible
  useEffect(() => {
    if (!pdfDocument) return;

    const renderPage = async (pageIndex: number) => {
      const pageInfo = pageData[pageIndex];
      if (!pageInfo || renderingPages.current.has(pageInfo.pageNumber)) return;

      renderingPages.current.add(pageInfo.pageNumber);

      try {
        const page = await pdfDocument.getPage(pageInfo.pageNumber);
        
        // Use shared canvas rendering utility
        const canvas = await renderPageToCanvas(page, { scale, createNew: true });
        
        // Cache the toDataURL result to avoid repeated expensive conversions
        const dataUrl = canvasToDataURL(canvas);

        setPageData(prev =>
          prev.map((p, i) =>
            i === pageIndex
              ? {
                  ...p,
                  canvas,
                  dataUrl,
                  isRendered: true,
                  height: viewport.height,
                  width: viewport.width,
                }
              : p
          )
        );
      } catch (error) {
        console.error(`Error rendering page ${pageInfo.pageNumber}:`, error);
      } finally {
        renderingPages.current.delete(pageInfo.pageNumber);
      }
    };

    // Render visible pages
    visiblePages.forEach(pageIndex => {
      if (!pageData[pageIndex]?.isRendered) {
        renderPage(pageIndex);
      }
    });

    // Update visibility status
    setPageData(prev =>
      prev.map((p, i) => ({
        ...p,
        isVisible: visiblePages.includes(i),
      }))
    );
  }, [visiblePages, pdfDocument, scale, pageData]);

  // Handle scroll events
  const handleScroll = useCallback(() => {
    if (!containerRef.current) return;

    const newScrollTop = containerRef.current.scrollTop;
    setScrollTop(newScrollTop);

    // Update current page based on scroll position
    let currentY = 0;
    let newCurrentPage = 1;

    for (let i = 0; i < pageData.length; i++) {
      const pageBottom = currentY + pageData[i].height + 20;

      if (newScrollTop < pageBottom - pageData[i].height / 2) {
        newCurrentPage = i + 1;
        break;
      }

      currentY = pageBottom;
      newCurrentPage = i + 1;
    }

    if (newCurrentPage !== currentPage) {
      onPageChange(newCurrentPage);
    }
  }, [pageData, currentPage, onPageChange]);

  // Setup scroll listener
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener('scroll', handleScroll, { passive: true });

    // Set initial container height
    const updateHeight = () => setContainerHeight(container.clientHeight);
    updateHeight();

    window.addEventListener('resize', updateHeight);

    return () => {
      container.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', updateHeight);
    };
  }, [handleScroll]);

  // Scroll to current page when it changes externally
  useEffect(() => {
    if (!containerRef.current || currentPage < 1 || currentPage > pageData.length) return;

    let targetY = 0;
    for (let i = 0; i < currentPage - 1; i++) {
      targetY += pageData[i].height + 20;
    }

    containerRef.current.scrollTo({
      top: targetY,
      behavior: 'smooth',
    });
  }, [currentPage, pageData]);

  // Calculate total height for scrollbar
  const totalHeight = useMemo(() => {
    return pageData.reduce((total, page) => total + page.height + 20, 0);
  }, [pageData]);

  // Memoize page positions to avoid recalculation in render
  const pagePositions = useMemo(() => {
    const positions: number[] = [];
    let currentY = 20; // Initial top padding
    
    for (let i = 0; i < pageData.length; i++) {
      positions.push(currentY);
      currentY += pageData[i].height + 20;
    }
    
    return positions;
  }, [pageData]);

  // Memory cleanup for non-visible pages
  useEffect(() => {
    const cleanup = () => {
      setPageData(prev =>
        prev.map(page => {
          if (!page.isVisible && page.canvas) {
            // Use shared cleanup utility
            cleanupCanvas(page.canvas);
            return { ...page, canvas: null, dataUrl: null, isRendered: false };
          }
          return page;
        })
      );
    };

    // Cleanup non-visible pages after a delay (reduced from 5s to 2s)
    const timeoutId = setTimeout(cleanup, MEMORY_CLEANUP_DELAY);
    return () => clearTimeout(timeoutId);
  }, [visiblePages]);

  if (!pdfDocument) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-gray-500">No document loaded</div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`overflow-auto h-full bg-gray-300 ${className}`}
      style={{ height: '100%' }}
    >
      <div
        style={{
          height: totalHeight,
          position: 'relative',
          paddingTop: '20px',
          paddingBottom: '20px',
        }}
      >
        {pageData.map((page, index) => {
          // Use memoized positions instead of recalculating
          const yPosition = pagePositions[index] || 20;

          return (
            <div
              key={page.pageNumber}
              style={{
                position: 'absolute',
                top: yPosition,
                left: '50%',
                transform: 'translateX(-50%)',
                width: page.width,
                height: page.height,
                marginBottom: '20px',
              }}
              className={`
                bg-white shadow-lg rounded-lg overflow-hidden border-2
                ${currentPage === page.pageNumber ? 'border-blue-500' : 'border-gray-200'}
              `}
            >
              {page.isRendered && page.dataUrl ? (
                <img
                  src={page.dataUrl}
                  alt={`Page ${page.pageNumber}`}
                  className="w-full h-full object-contain"
                  style={{ width: page.width, height: page.height }}
                />
              ) : page.isVisible ? (
                <div className="w-full h-full flex items-center justify-center bg-gray-100">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
                    <div className="text-sm text-gray-600">Loading page {page.pageNumber}...</div>
                  </div>
                </div>
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gray-50">
                  <div className="text-gray-400 text-sm">Page {page.pageNumber}</div>
                </div>
              )}

              {/* Page Number Overlay */}
              {showPageNumbers && (
                <div className="absolute bottom-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                  {page.pageNumber}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
