/**
 * PDF service for loading, rendering, and managing PDF documents.
 * Handles document caching, page rendering, text layers, and annotations.
 */

import * as pdfjsLib from 'pdfjs-dist';
import type { PDFDocumentProxy, PDFPageProxy, RenderTask } from 'pdfjs-dist';

// Configure PDF.js worker - use local worker for reliability
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString();

// Extended canvas interface for PDF rendering state
interface ExtendedHTMLCanvasElement extends HTMLCanvasElement {
  _isRendering?: boolean;
  _pdfRenderTask?: RenderTask | null;
}

/**
 * Service class for PDF operations using PDF.js.
 * Provides static methods for document loading, page retrieval, and rendering.
 */
export class PDFService {
  private static loadedDocuments = new Map<string, PDFDocumentProxy>();

  /**
   * Load a PDF document from a URL.
   * Documents are cached to avoid redundant loads.
   *
   * @param url - The URL of the PDF document to load
   * @returns Promise resolving to the loaded PDF document
   * @throws Error if document fails to load
   */
  static async loadDocument(url: string): Promise<PDFDocumentProxy> {
    try {
      console.log('🔗 [PDFService] Loading document from URL:', {
        url,
        workerSrc: pdfjsLib.GlobalWorkerOptions.workerSrc,
        version: pdfjsLib.version,
      });

      // Check if document is already loaded
      if (this.loadedDocuments.has(url)) {
        console.log('💾 [PDFService] Document found in cache');
        return this.loadedDocuments.get(url)!;
      }

      console.log('⚙️ [PDFService] Creating PDF.js loading task...');
      const loadingTask = pdfjsLib.getDocument({
        url,
        cMapUrl: `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/cmaps/`,
        cMapPacked: true,
        enableXfa: true, // Enable XFA form support
      });

      console.log('⏳ [PDFService] Waiting for document to load...');
      const document = await loadingTask.promise;

      console.log('✅ [PDFService] Document loaded successfully:', {
        numPages: document.numPages,
        fingerprint: document.fingerprints?.[0] || 'unknown',
      });

      this.loadedDocuments.set(url, document);

      return document;
    } catch (error) {
      console.error('❌ [PDFService] Error loading PDF document:', {
        url,
        error,
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined,
      });
      throw new Error('Failed to load PDF document');
    }
  }

  /**
   * Get a specific page from a loaded PDF document.
   *
   * @param document - The loaded PDF document
   * @param pageNumber - The page number to retrieve (1-indexed)
   * @returns Promise resolving to the requested page
   * @throws Error if page fails to load
   */
  static async getPage(document: PDFDocumentProxy, pageNumber: number): Promise<PDFPageProxy> {
    try {
      console.log('📄 [PDFService] Getting page from document:', {
        pageNumber,
        totalPages: document.numPages,
        documentFingerprint: document.fingerprints?.[0] || 'unknown',
      });

      const page = await document.getPage(pageNumber);

      console.log('✅ [PDFService] Page retrieved successfully:', {
        pageNumber: page.pageNumber,
        hasViewport: typeof page.getViewport === 'function',
      });

      return page;
    } catch (error) {
      console.error(`❌ [PDFService] Error loading page ${pageNumber}:`, {
        error,
        message: error instanceof Error ? error.message : 'Unknown error',
        pageNumber,
        totalPages: document.numPages,
      });
      throw new Error(`Failed to load page ${pageNumber}`);
    }
  }

  /**
   * Render a PDF page to a canvas element.
   * Handles concurrent render prevention and task cancellation.
   *
   * @param page - The PDF page to render
   * @param canvas - The canvas element to render to
   * @param scale - The scale factor for rendering (default: 1.0)
   * @returns Promise that resolves when rendering is complete
   * @throws Error if rendering fails (except for cancellations)
   */
  static async renderPageToCanvas(
    page: PDFPageProxy,
    canvas: HTMLCanvasElement,
    scale: number = 1.0
  ): Promise<void> {
    // Check if canvas is already being rendered
    const extendedCanvas = canvas as ExtendedHTMLCanvasElement;
    
    try {
      if (extendedCanvas._isRendering) {
        console.log('⏭️ [PDFService] Canvas already rendering, skipping duplicate request');
        return;
      }

      // Mark canvas as being rendered
      extendedCanvas._isRendering = true;

      const viewport = page.getViewport({ scale });
      const context = canvas.getContext('2d');

      if (!context) {
        throw new Error('Failed to get canvas context');
      }

      // Cancel any ongoing render operations on this canvas
      const existingTask = extendedCanvas._pdfRenderTask;
      if (existingTask) {
        console.log('🔄 [PDFService] Cancelling existing render task');
        await existingTask.cancel();
      }

      // Clear any existing content
      context.clearRect(0, 0, canvas.width, canvas.height);

      canvas.width = viewport.width;
      canvas.height = viewport.height;

      const renderContext = {
        canvasContext: context,
        viewport: viewport,
      };

      const renderTask = page.render(renderContext);
      extendedCanvas._pdfRenderTask = renderTask;

      await renderTask.promise;

      // Successfully completed
      extendedCanvas._pdfRenderTask = null;
      extendedCanvas._isRendering = false;
    } catch (error) {
      // Always clean up state
      extendedCanvas._pdfRenderTask = null;
      extendedCanvas._isRendering = false;

      // Handle cancellation gracefully - this is expected in React 18 Strict Mode
      if (
        error &&
        typeof error === 'object' &&
        'name' in error &&
        error.name === 'RenderingCancelledException'
      ) {
        const errorObj = error as { message?: string };
        console.log('ℹ️ [PDFService] Render cancelled (expected in development):', {
          message: errorObj.message,
          pageNumber: errorObj.message?.match(/page (\d+)/)?.[1] || 'unknown',
        });
        return; // Don't throw error for cancellations
      }

      console.error('❌ [PDFService] Error rendering page to canvas:', error);
      throw new Error('Failed to render page');
    }
  }

  /**
   * Render the text layer for a PDF page.
   * Enables text selection and search functionality.
   *
   * @param page - The PDF page to render text layer for
   * @param textLayerDiv - The div element to render the text layer into
   * @param scale - The scale factor for rendering (default: 1.0)
   * @returns Promise that resolves when text layer is rendered
   */
  static async renderTextLayer(
    page: PDFPageProxy,
    textLayerDiv: HTMLDivElement,
    scale: number = 1.0
  ): Promise<void> {
    try {
      if (!textLayerDiv) {
        console.warn('⚠️ [PDFService] Text layer div is null, skipping text layer rendering');
        return;
      }

      const viewport = page.getViewport({ scale });
      const textContent = await page.getTextContent();

      // Clear previous content
      textLayerDiv.innerHTML = '';
      textLayerDiv.style.position = 'absolute';
      textLayerDiv.style.left = '0';
      textLayerDiv.style.top = '0';
      textLayerDiv.style.right = '0';
      textLayerDiv.style.bottom = '0';
      textLayerDiv.style.overflow = 'hidden';
      textLayerDiv.style.opacity = '0.2';
      textLayerDiv.style.lineHeight = '1.0';

      // Render text layer (for text selection and search)
      const textLayer = new pdfjsLib.TextLayer({
        textContentSource: textContent,
        container: textLayerDiv,
        viewport: viewport,
      });

      await textLayer.render();
    } catch (error) {
      console.error('❌ [PDFService] Error rendering text layer:', error);
      // Don't throw error for text layer - it's not critical
    }
  }

  /**
   * Render the annotation layer for a PDF page.
   * Currently a simplified implementation for POC.
   *
   * @param page - The PDF page to render annotations for
   * @param annotationLayerDiv - The div element to render annotations into
   * @param _scale - The scale factor (currently unused)
   * @returns Promise that resolves when annotation layer is rendered
   */
  static async renderAnnotationLayer(
    page: PDFPageProxy,
    annotationLayerDiv: HTMLDivElement,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    _scale: number = 1.0
  ): Promise<void> {
    try {
      if (!annotationLayerDiv) {
        console.warn(
          '⚠️ [PDFService] Annotation layer div is null, skipping annotation layer rendering'
        );
        return;
      }

      const annotations = await page.getAnnotations();

      // Clear previous content
      annotationLayerDiv.innerHTML = '';
      annotationLayerDiv.style.position = 'absolute';
      annotationLayerDiv.style.left = '0';
      annotationLayerDiv.style.top = '0';
      annotationLayerDiv.style.right = '0';
      annotationLayerDiv.style.bottom = '0';
      annotationLayerDiv.style.overflow = 'hidden';

      // For now, just render basic annotation info
      if (annotations.length > 0) {
        console.log(`Found ${annotations.length} annotations on page`, annotations);
        // TODO: Implement full annotation layer rendering
        // This is a simplified version for the POC
      }
    } catch (error) {
      console.error('❌ [PDFService] Error rendering annotation layer:', error);
      // Don't throw error for annotation layer - it's not critical
    }
  }

  /**
   * Clean up loaded PDF documents from cache.
   *
   * @param document - Optional specific document to clean up. If not provided, cleans all.
   */
  static cleanup(document?: PDFDocumentProxy): void {
    if (document) {
      // Clean up specific document
      const url = Array.from(this.loadedDocuments.entries()).find(
        ([, doc]) => doc === document
      )?.[0];
      if (url) {
        this.loadedDocuments.delete(url);
      }
    } else {
      // Clean up all documents
      this.loadedDocuments.clear();
    }
  }

  /**
   * Get a copy of all currently loaded documents.
   *
   * @returns Map of document URLs to their loaded PDF document objects
   */
  static getLoadedDocuments(): Map<string, PDFDocumentProxy> {
    return new Map(this.loadedDocuments);
  }
}
