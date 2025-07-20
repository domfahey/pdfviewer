import React, { useEffect, useRef, useCallback } from 'react';
import type { PDFPageProxy } from 'pdfjs-dist';
import { PDFService } from '../../services/pdfService';

interface PDFPageProps {
  page: PDFPageProxy;
  scale: number;
  className?: string;
  onPageRender?: () => void;
  onPageError?: (error: string) => void;
}

export const PDFPage: React.FC<PDFPageProps> = ({
  page,
  scale,
  className = '',
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
    // Wait a tiny bit to handle React 18 Strict Mode double effects
    await new Promise(resolve => setTimeout(resolve, 0));
    
    // Skip render if component is not mounted
    if (!isMountedRef.current) {
      console.log('⏭️ [PDFPage] Skipping render, component not mounted');
      return;
    }

    if (!canvasRef.current) {
      console.warn('⚠️ [PDFPage] Canvas ref not available, skipping render');
      return;
    }

    try {
      console.log('🎨 [PDFPage] Starting page render:', {
        pageNumber: page.pageNumber,
        scale,
        canvasExists: !!canvasRef.current,
        textLayerExists: !!textLayerRef.current,
        annotationLayerExists: !!annotationLayerRef.current,
        isMounted: isMountedRef.current
      });

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
        console.log('✅ [PDFPage] Page render completed successfully');
        onPageRender?.();
      }
    } catch (error) {
      // Only log errors if not caused by unmounting and it's a real error
      if (isMountedRef.current) {
        console.error('❌ [PDFPage] Error rendering page:', error);
        onPageError?.(error instanceof Error ? error.message : 'Failed to render page');
      }
    }
  }, [page.pageNumber, scale]); // Stable dependencies only

  useEffect(() => {
    renderPage();
  }, [renderPage]);

  // Clean up on unmount
  useEffect(() => {
    isMountedRef.current = true;
    
    return () => {
      console.log('🧹 [PDFPage] Component unmounting, cleaning up');
      isMountedRef.current = false;
      
      const canvas = canvasRef.current;
      const textLayer = textLayerRef.current;
      const annotationLayer = annotationLayerRef.current;
      
      // Cancel any ongoing render tasks
      if (canvas && (canvas as any)._pdfRenderTask) {
        console.log('🛑 [PDFPage] Cancelling render task on unmount');
        (canvas as any)._pdfRenderTask.cancel();
        (canvas as any)._pdfRenderTask = null;
        (canvas as any)._isRendering = false;
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
      className={`relative inline-block bg-white shadow-lg ${className}`}
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
    </div>
  );
};
