/**
 * Canvas rendering utilities for PDF pages.
 *
 * Consolidates canvas creation and rendering logic shared across
 * PDFPage, VirtualPDFViewer, and PDFThumbnails components.
 */

import type { PDFPageProxy } from 'pdfjs-dist';

export interface RenderOptions {
  scale: number;
  canvas?: HTMLCanvasElement;
  createNew?: boolean;
}

export interface CanvasCleanupExtensions {
  _pdfRenderTask?: { cancel: () => void } | null;
  _isRendering?: boolean;
}

/**
 * Create and configure a canvas for PDF rendering.
 *
 * @param width - Canvas width in pixels
 * @param height - Canvas height in pixels
 * @param existingCanvas - Optional existing canvas to reuse
 * @returns Configured canvas element
 */
export function createCanvas(
  width: number,
  height: number,
  existingCanvas?: HTMLCanvasElement
): HTMLCanvasElement {
  const canvas = existingCanvas || document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  return canvas;
}

/**
 * Render a PDF page to a canvas element.
 *
 * @param page - PDF page proxy to render
 * @param options - Rendering options (scale, canvas)
 * @returns Promise that resolves with the rendered canvas
 * @throws Error if rendering fails
 */
export async function renderPageToCanvas(
  page: PDFPageProxy,
  options: RenderOptions
): Promise<HTMLCanvasElement> {
  const { scale, canvas: existingCanvas, createNew = false } = options;

  const viewport = page.getViewport({ scale });
  const canvas = createNew
    ? createCanvas(viewport.width, viewport.height)
    : createCanvas(viewport.width, viewport.height, existingCanvas);

  const context = canvas.getContext('2d');

  if (!context) {
    throw new Error('Failed to get canvas 2D context');
  }

  const renderContext = {
    canvasContext: context,
    viewport: viewport,
  };

  await page.render(renderContext).promise;

  return canvas;
}

/**
 * Clear and clean up a canvas element.
 *
 * Cancels any ongoing render tasks and clears the canvas content.
 * Useful for cleanup during component unmount or when switching pages.
 *
 * @param canvas - Canvas element to clean up
 */
export function cleanupCanvas(canvas: HTMLCanvasElement | null): void {
  if (!canvas) return;

  // Cancel any ongoing render tasks
  const extendedCanvas = canvas as HTMLCanvasElement & CanvasCleanupExtensions;
  if (extendedCanvas._pdfRenderTask) {
    extendedCanvas._pdfRenderTask.cancel();
    extendedCanvas._pdfRenderTask = null;
    extendedCanvas._isRendering = false;
  }

  // Clear canvas content
  const context = canvas.getContext('2d');
  if (context) {
    context.clearRect(0, 0, canvas.width, canvas.height);
  }
}

/**
 * Convert a canvas to a data URL for caching or display.
 *
 * @param canvas - Canvas element to convert
 * @param type - Image MIME type (default: 'image/png')
 * @returns Data URL string
 */
export function canvasToDataURL(canvas: HTMLCanvasElement, type = 'image/png'): string {
  return canvas.toDataURL(type);
}
