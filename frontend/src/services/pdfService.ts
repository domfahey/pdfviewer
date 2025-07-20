import * as pdfjsLib from 'pdfjs-dist';
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist';

// Configure PDF.js worker - use local worker for reliability
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString();

export class PDFService {
  private static loadedDocuments = new Map<string, PDFDocumentProxy>();

  static async loadDocument(url: string): Promise<PDFDocumentProxy> {
    try {
      console.log('🔗 [PDFService] Loading document from URL:', {
        url,
        workerSrc: pdfjsLib.GlobalWorkerOptions.workerSrc,
        version: pdfjsLib.version
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
        fingerprint: document.fingerprints?.[0] || 'unknown'
      });

      this.loadedDocuments.set(url, document);

      return document;
    } catch (error) {
      console.error('❌ [PDFService] Error loading PDF document:', {
        url,
        error,
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
      throw new Error('Failed to load PDF document');
    }
  }

  static async getPage(document: PDFDocumentProxy, pageNumber: number): Promise<PDFPageProxy> {
    try {
      console.log('📄 [PDFService] Getting page from document:', {
        pageNumber,
        totalPages: document.numPages,
        documentFingerprint: document.fingerprints?.[0] || 'unknown'
      });
      
      const page = await document.getPage(pageNumber);
      
      console.log('✅ [PDFService] Page retrieved successfully:', {
        pageNumber: page.pageNumber,
        hasViewport: typeof page.getViewport === 'function'
      });
      
      return page;
    } catch (error) {
      console.error(`❌ [PDFService] Error loading page ${pageNumber}:`, {
        error,
        message: error instanceof Error ? error.message : 'Unknown error',
        pageNumber,
        totalPages: document.numPages
      });
      throw new Error(`Failed to load page ${pageNumber}`);
    }
  }

  static async renderPageToCanvas(
    page: PDFPageProxy,
    canvas: HTMLCanvasElement,
    scale: number = 1.0
  ): Promise<void> {
    try {
      // Check if canvas is already being rendered
      if ((canvas as any)._isRendering) {
        console.log('⏭️ [PDFService] Canvas already rendering, skipping duplicate request');
        return;
      }

      // Mark canvas as being rendered
      (canvas as any)._isRendering = true;

      const viewport = page.getViewport({ scale });
      const context = canvas.getContext('2d');

      if (!context) {
        throw new Error('Failed to get canvas context');
      }

      // Cancel any ongoing render operations on this canvas
      const existingTask = (canvas as any)._pdfRenderTask;
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
      (canvas as any)._pdfRenderTask = renderTask;

      await renderTask.promise;
      
      // Successfully completed
      (canvas as any)._pdfRenderTask = null;
      (canvas as any)._isRendering = false;
      
    } catch (error) {
      // Always clean up state
      (canvas as any)._pdfRenderTask = null;
      (canvas as any)._isRendering = false;
      
      // Handle cancellation gracefully - this is expected in React 18 Strict Mode
      if (error && typeof error === 'object' && 'name' in error && error.name === 'RenderingCancelledException') {
        console.log('ℹ️ [PDFService] Render cancelled (expected in development):', {
          message: (error as any).message,
          pageNumber: (error as any).message?.match(/page (\d+)/)?.[1] || 'unknown'
        });
        return; // Don't throw error for cancellations
      }
      
      console.error('❌ [PDFService] Error rendering page to canvas:', error);
      throw new Error('Failed to render page');
    }
  }

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

  static async renderAnnotationLayer(
    page: PDFPageProxy,
    annotationLayerDiv: HTMLDivElement,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    _scale: number = 1.0
  ): Promise<void> {
    try {
      if (!annotationLayerDiv) {
        console.warn('⚠️ [PDFService] Annotation layer div is null, skipping annotation layer rendering');
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

  static getLoadedDocuments(): Map<string, PDFDocumentProxy> {
    return new Map(this.loadedDocuments);
  }
}
