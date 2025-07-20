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

  const renderPage = useCallback(async () => {
    if (!canvasRef.current || !textLayerRef.current || !annotationLayerRef.current) {
      return;
    }

    try {
      // Render canvas layer
      await PDFService.renderPageToCanvas(page, canvasRef.current, scale);

      // Render text layer for text selection and search
      await PDFService.renderTextLayer(page, textLayerRef.current, scale);

      // Render annotation layer for interactive elements
      await PDFService.renderAnnotationLayer(page, annotationLayerRef.current, scale);

      onPageRender?.();
    } catch (error) {
      console.error('Error rendering page:', error);
      onPageError?.(error instanceof Error ? error.message : 'Failed to render page');
    }
  }, [page, scale, onPageRender, onPageError]);

  useEffect(() => {
    renderPage();
  }, [renderPage]);

  // Clean up on unmount
  useEffect(() => {
    const canvas = canvasRef.current;
    return () => {
      if (canvas) {
        const context = canvas.getContext('2d');
        if (context) {
          context.clearRect(0, 0, canvas.width, canvas.height);
        }
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
