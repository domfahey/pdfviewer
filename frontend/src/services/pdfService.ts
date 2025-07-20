import * as pdfjsLib from 'pdfjs-dist';
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist';

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

export class PDFService {
  private static loadedDocuments = new Map<string, PDFDocumentProxy>();

  static async loadDocument(url: string): Promise<PDFDocumentProxy> {
    try {
      // Check if document is already loaded
      if (this.loadedDocuments.has(url)) {
        return this.loadedDocuments.get(url)!;
      }

      const loadingTask = pdfjsLib.getDocument({
        url,
        cMapUrl: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/',
        cMapPacked: true,
        enableXfa: true, // Enable XFA form support
      });

      const document = await loadingTask.promise;
      this.loadedDocuments.set(url, document);

      return document;
    } catch (error) {
      console.error('Error loading PDF document:', error);
      throw new Error('Failed to load PDF document');
    }
  }

  static async getPage(document: PDFDocumentProxy, pageNumber: number): Promise<PDFPageProxy> {
    try {
      return await document.getPage(pageNumber);
    } catch (error) {
      console.error(`Error loading page ${pageNumber}:`, error);
      throw new Error(`Failed to load page ${pageNumber}`);
    }
  }

  static async renderPageToCanvas(
    page: PDFPageProxy,
    canvas: HTMLCanvasElement,
    scale: number = 1.0
  ): Promise<void> {
    try {
      const viewport = page.getViewport({ scale });
      const context = canvas.getContext('2d');

      if (!context) {
        throw new Error('Failed to get canvas context');
      }

      canvas.width = viewport.width;
      canvas.height = viewport.height;

      const renderContext = {
        canvasContext: context,
        viewport: viewport,
      };

      await page.render(renderContext).promise;
    } catch (error) {
      console.error('Error rendering page to canvas:', error);
      throw new Error('Failed to render page');
    }
  }

  static async renderTextLayer(
    page: PDFPageProxy,
    textLayerDiv: HTMLDivElement,
    scale: number = 1.0
  ): Promise<void> {
    try {
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
      console.error('Error rendering text layer:', error);
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
      console.error('Error rendering annotation layer:', error);
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
