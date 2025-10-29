import React, { useEffect, useRef, useCallback } from 'react';
import type { PDFPageProxy } from 'pdfjs-dist';
import { PDFService } from '../../services/pdfService';
import { PDFSearchHighlight } from './PDFSearchHighlight';

interface PDFPageProps {
  page: PDFPageProxy;
  scale: number;
  className?: string;
  searchQuery?: string;
  isCurrentSearchPage?: boolean;
  onPageRender?: () => void;
  onPageError?: (error: string) => void;
}

export const PDFPage: React.FC<PDFPageProps> = ({
  page,
  scale,
  className = '',
  searchQuery = '',
  isCurrentSearchPage = false,
  onPageRender,
  onPageError,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const textLayerRef = useRef<HTMLDivElement>(null);
  const annotationLayerRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Track mounting state - MUST be declared before using in renderPage
  const isMountedRef = useRef(true);

  const renderPage = useCallback(async () => {
    // Skip render if component is not mounted
    if (!isMountedRef.current) {
      return;
    }

    if (!canvasRef.current) {
      return;
    }

    try {
      // Render canvas layer (required)
      await PDFService.renderPageToCanvas(page, canvasRef.current, scale);

      // Check if still mounted after async operation
      if (!isMountedRef.current) return;

      // Render text layer for text selection and search (optional)
      if (textLayerRef.current) {
        await PDFService.renderTextLayer(page, textLayerRef.current, scale);
      }

      if (!isMountedRef.current) return;

      // Render annotation layer for interactive elements (optional)
      if (annotationLayerRef.current) {
        await PDFService.renderAnnotationLayer(page, annotationLayerRef.current, scale);
      }

      // Only call success callback if component is still mounted
      if (isMountedRef.current) {
        onPageRender?.();
      }
    } catch (error) {
      // Only report errors if component is still mounted
      if (isMountedRef.current) {
        console.error('Error rendering PDF page:', error);
        onPageError?.(error instanceof Error ? error.message : 'Failed to render page');
      }
    }
  }, [scale, onPageError, onPageRender, page]);

  useEffect(() => {
    renderPage();
  }, [renderPage]);

  // Clean up on unmount
  useEffect(() => {
    isMountedRef.current = true;

    // Capture current ref values when effect runs
    const canvas = canvasRef.current;
    const textLayer = textLayerRef.current;
    const annotationLayer = annotationLayerRef.current;

    return () => {
      isMountedRef.current = false;

      // Cancel any ongoing render tasks
      interface ExtendedCanvas extends HTMLCanvasElement {
        _pdfRenderTask?: { cancel: () => void } | null;
        _isRendering?: boolean;
      }
      if (canvas) {
        const extendedCanvas = canvas as ExtendedCanvas;
        if (extendedCanvas._pdfRenderTask) {
          extendedCanvas._pdfRenderTask.cancel();
          extendedCanvas._pdfRenderTask = null;
          extendedCanvas._isRendering = false;
        }
      }

      // Clear canvas
      if (canvas) {
        const context = canvas.getContext('2d');
        if (context) {
          context.clearRect(0, 0, canvas.width, canvas.height);
        }
      }

      // Clear text layer
      if (textLayer) {
        textLayer.innerHTML = '';
      }

      // Clear annotation layer
      if (annotationLayer) {
        annotationLayer.innerHTML = '';
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className={`relative inline-block bg-white shadow-md ${className}`}
      style={{
        marginBottom: '20px',
      }}
    >
      {/* Canvas layer - renders the PDF page */}
      <canvas
        ref={canvasRef}
        className="block"
        style={{
          display: 'block',
          maxWidth: '100%',
          height: 'auto',
        }}
      />

      {/* Text layer - enables text selection and search */}
      <div
        ref={textLayerRef}
        className="absolute inset-0 overflow-hidden"
        style={{
          pointerEvents: 'auto',
          userSelect: 'text',
        }}
      />

      {/* Annotation layer - renders interactive PDF elements */}
      <div
        ref={annotationLayerRef}
        className="absolute inset-0 overflow-hidden"
        style={{
          pointerEvents: 'auto',
        }}
      />

      {/* Search highlight layer */}
      <PDFSearchHighlight
        searchQuery={searchQuery}
        textLayer={textLayerRef.current}
        isCurrentPage={isCurrentSearchPage}
      />
    </div>
  );
};
