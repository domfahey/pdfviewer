import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { PDFService } from '../pdfService';
import type { PDFDocumentProxy, PDFPageProxy, RenderTask } from 'pdfjs-dist';

// Mock PDF.js
vi.mock('pdfjs-dist', () => ({
  GlobalWorkerOptions: {
    workerSrc: '',
  },
  version: '3.11.174',
  getDocument: vi.fn(),
  TextLayer: vi.fn(),
}));

// Import the mocked module
import * as pdfjsLib from 'pdfjs-dist';
const mockPDFJS = vi.mocked(pdfjsLib);

// Mock types for testing
interface MockRenderTask extends RenderTask {
  cancel: () => Promise<void>;
  promise: Promise<void>;
}

const createMockRenderTask = (shouldReject = false): MockRenderTask =>
  ({
    cancel: vi.fn().mockResolvedValue(undefined),
    promise: shouldReject ? Promise.reject(new Error('Render failed')) : Promise.resolve(),
  }) as MockRenderTask;

const createMockPage = (pageNumber: number): PDFPageProxy =>
  ({
    pageNumber,
    getViewport: vi.fn((params: { scale: number }) => ({
      width: 800 * params.scale,
      height: 600 * params.scale,
      scale: params.scale,
    })),
    render: vi.fn(() => createMockRenderTask()),
    getTextContent: vi.fn().mockResolvedValue({
      items: [{ str: 'Sample text content' }, { str: 'More text' }],
      styles: {},
    }),
    getAnnotations: vi.fn().mockResolvedValue([]),
    cleanup: vi.fn(),
    stats: null,
    ref: { num: pageNumber, gen: 0 },
    rotate: 0,
    view: [0, 0, 800, 600],
    userUnit: 1,
    getOperatorList: vi.fn(),
    streamTextContent: vi.fn(),
    getDisplayReadableText: vi.fn(),
    getStructTree: vi.fn(),
    transport: {} as object,
    objs: {} as object,
    commonObjs: {} as object,
    fontCache: {} as object,
    builtInCMapCache: {} as object,
    standardFontDataCache: {} as object,
    systemFontCache: {} as object,
    rendered: Promise.resolve(),
  }) as PDFPageProxy;

const createMockDocument = (numPages: number = 5): PDFDocumentProxy =>
  ({
    numPages,
    fingerprints: ['mock-fingerprint-123'],
    getPage: vi.fn((pageNum: number) => Promise.resolve(createMockPage(pageNum))),
    loadingTask: {} as object,
    getPageIndex: vi.fn(),
    getDestinations: vi.fn(),
    getDestination: vi.fn(),
    getPageLabels: vi.fn(),
    getPageLayout: vi.fn(),
    getPageMode: vi.fn(),
    getViewerPreferences: vi.fn(),
    getMetadata: vi.fn(),
    getMarkInfo: vi.fn(),
    getData: vi.fn(),
    saveDocument: vi.fn(),
    getDownloadInfo: vi.fn(),
    cleanup: vi.fn(),
    destroy: vi.fn(),
    cachedPageNumber: 1,
    loadingParams: {} as object,
    transport: {} as object,
    getDocumentId: vi.fn(),
    getOptionalContentConfig: vi.fn(),
    getPermissions: vi.fn(),
    getJSActions: vi.fn(),
    getFieldObjects: vi.fn(),
    hasJSActions: vi.fn(),
    getCalculationOrderIds: vi.fn(),
    getOutline: vi.fn(),
    getAttachments: vi.fn(),
    getJavaScript: vi.fn(),
    getPageLabel: vi.fn(),
    isPureXfa: false,
    allXfaHtml: false,
  }) as PDFDocumentProxy;

const createMockCanvas = (): HTMLCanvasElement => {
  const canvas = document.createElement('canvas');
  const context = {
    clearRect: vi.fn(),
    drawImage: vi.fn(),
    getImageData: vi.fn(),
    putImageData: vi.fn(),
  };

  vi.spyOn(canvas, 'getContext').mockReturnValue(context as RenderingContext);
  return canvas;
};

const createMockTextLayer = () => ({
  render: vi.fn().mockResolvedValue(undefined),
});

describe('PDFService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset the loaded documents cache
    PDFService.cleanup();

    // Setup default mocks
    mockPDFJS.TextLayer.mockImplementation(() => createMockTextLayer());
  });

  afterEach(() => {
    PDFService.cleanup();
  });

  describe('loadDocument', () => {
    it('should successfully load a PDF document', async () => {
      const mockDocument = createMockDocument(10);
      const mockLoadingTask = {
        promise: Promise.resolve(mockDocument),
      };

      mockPDFJS.getDocument.mockReturnValue(mockLoadingTask);

      const testUrl = 'http://example.com/test.pdf';
      const result = await PDFService.loadDocument(testUrl);

      expect(mockPDFJS.getDocument).toHaveBeenCalledWith({
        url: testUrl,
        cMapUrl: expect.stringContaining('cmaps'),
        cMapPacked: true,
        enableXfa: true,
      });

      expect(result).toBe(mockDocument);
      expect(result.numPages).toBe(10);
    });

    it('should cache loaded documents', async () => {
      const mockDocument = createMockDocument(5);
      const mockLoadingTask = {
        promise: Promise.resolve(mockDocument),
      };

      mockPDFJS.getDocument.mockReturnValue(mockLoadingTask);

      const testUrl = 'http://example.com/test.pdf';

      // Load document first time
      const result1 = await PDFService.loadDocument(testUrl);

      // Load same document again
      const result2 = await PDFService.loadDocument(testUrl);

      expect(mockPDFJS.getDocument).toHaveBeenCalledTimes(1); // Should be cached
      expect(result1).toBe(result2);
      expect(result1).toBe(mockDocument);
    });

    it('should handle loading errors', async () => {
      const mockLoadingTask = {
        promise: Promise.reject(new Error('Network error')),
      };

      mockPDFJS.getDocument.mockReturnValue(mockLoadingTask);

      const testUrl = 'http://example.com/invalid.pdf';

      await expect(PDFService.loadDocument(testUrl)).rejects.toThrow('Failed to load PDF document');
    });

    it('should handle non-Error exceptions', async () => {
      const mockLoadingTask = {
        promise: Promise.reject('String error'),
      };

      mockPDFJS.getDocument.mockReturnValue(mockLoadingTask);

      await expect(PDFService.loadDocument('test.pdf')).rejects.toThrow(
        'Failed to load PDF document'
      );
    });

    it('should configure worker source correctly', async () => {
      const mockDocument = createMockDocument(1);
      const mockLoadingTask = {
        promise: Promise.resolve(mockDocument),
      };

      mockPDFJS.getDocument.mockReturnValue(mockLoadingTask);

      await PDFService.loadDocument('test.pdf');

      expect(mockPDFJS.GlobalWorkerOptions.workerSrc).toBeTruthy();
    });
  });

  describe('getPage', () => {
    it('should successfully get a page from document', async () => {
      const mockDocument = createMockDocument(5);
      const mockPage = createMockPage(3);

      mockDocument.getPage = vi.fn().mockResolvedValue(mockPage);

      const result = await PDFService.getPage(mockDocument, 3);

      expect(mockDocument.getPage).toHaveBeenCalledWith(3);
      expect(result).toBe(mockPage);
      expect(result.pageNumber).toBe(3);
    });

    it('should handle page loading errors', async () => {
      const mockDocument = createMockDocument(5);
      mockDocument.getPage = vi.fn().mockRejectedValue(new Error('Page not found'));

      await expect(PDFService.getPage(mockDocument, 10)).rejects.toThrow('Failed to load page 10');
    });

    it('should handle invalid page numbers', async () => {
      const mockDocument = createMockDocument(5);
      mockDocument.getPage = vi.fn().mockRejectedValue(new Error('Invalid page number'));

      await expect(PDFService.getPage(mockDocument, 0)).rejects.toThrow('Failed to load page 0');
    });
  });

  describe('renderPageToCanvas', () => {
    it('should successfully render page to canvas', async () => {
      const mockPage = createMockPage(1);
      const canvas = createMockCanvas();
      const scale = 1.5;

      mockPage.render = vi.fn(() => createMockRenderTask());

      await PDFService.renderPageToCanvas(mockPage, canvas, scale);

      expect(mockPage.getViewport).toHaveBeenCalledWith({ scale });
      expect(mockPage.render).toHaveBeenCalledWith({
        canvasContext: expect.any(Object),
        viewport: expect.any(Object),
      });

      expect(canvas.width).toBe(800 * scale);
      expect(canvas.height).toBe(600 * scale);
    });

    it('should handle canvas without context', async () => {
      const mockPage = createMockPage(1);
      const canvas = createMockCanvas();

      vi.spyOn(canvas, 'getContext').mockReturnValue(null);

      await expect(PDFService.renderPageToCanvas(mockPage, canvas)).rejects.toThrow(
        'Failed to get canvas context'
      );
    });

    it('should prevent duplicate rendering on same canvas', async () => {
      const mockPage = createMockPage(1);
      const canvas = createMockCanvas();

      // Mark canvas as already rendering
      (canvas as unknown as { _isRendering: boolean })._isRendering = true;

      await PDFService.renderPageToCanvas(mockPage, canvas);

      expect(mockPage.render).not.toHaveBeenCalled();
    });

    it('should cancel existing render task before new render', async () => {
      const mockPage = createMockPage(1);
      const canvas = createMockCanvas();

      const existingTask = createMockRenderTask();
      (canvas as unknown as { _pdfRenderTask: object })._pdfRenderTask = existingTask;

      await PDFService.renderPageToCanvas(mockPage, canvas);

      expect(existingTask.cancel).toHaveBeenCalled();
    });

    it('should handle rendering cancellation gracefully', async () => {
      const mockPage = createMockPage(1);
      const canvas = createMockCanvas();

      const cancelledError = {
        name: 'RenderingCancelledException',
        message: 'Rendering cancelled for page 1',
      };

      mockPage.render = vi.fn(() => ({
        cancel: vi.fn(),
        promise: Promise.reject(cancelledError),
      }));

      // Should not throw error for cancellation
      await expect(PDFService.renderPageToCanvas(mockPage, canvas)).resolves.toBeUndefined();
    });

    it('should handle render errors', async () => {
      const mockPage = createMockPage(1);
      const canvas = createMockCanvas();

      mockPage.render = vi.fn(() => createMockRenderTask(true));

      await expect(PDFService.renderPageToCanvas(mockPage, canvas)).rejects.toThrow(
        'Failed to render page'
      );
    });

    it('should clear canvas before rendering', async () => {
      const mockPage = createMockPage(1);
      const canvas = createMockCanvas();
      const context = canvas.getContext('2d')!;

      await PDFService.renderPageToCanvas(mockPage, canvas);

      expect(context.clearRect).toHaveBeenCalledWith(0, 0, canvas.width, canvas.height);
    });
  });

  describe('renderTextLayer', () => {
    it('should successfully render text layer', async () => {
      const mockPage = createMockPage(1);
      const textLayerDiv = document.createElement('div');
      const scale = 1.0;

      const mockTextLayer = createMockTextLayer();
      mockPDFJS.TextLayer.mockImplementation(() => mockTextLayer);

      await PDFService.renderTextLayer(mockPage, textLayerDiv, scale);

      expect(mockPage.getTextContent).toHaveBeenCalled();
      expect(mockPDFJS.TextLayer).toHaveBeenCalledWith({
        textContentSource: expect.any(Object),
        container: textLayerDiv,
        viewport: expect.any(Object),
      });
      expect(mockTextLayer.render).toHaveBeenCalled();

      // Check that div was styled
      expect(textLayerDiv.style.position).toBe('absolute');
      expect(textLayerDiv.style.opacity).toBe('0.2');
    });

    it('should handle null text layer div gracefully', async () => {
      const mockPage = createMockPage(1);

      // Should not throw error
      await expect(
        PDFService.renderTextLayer(mockPage, null as unknown as HTMLDivElement)
      ).resolves.toBeUndefined();

      expect(mockPage.getTextContent).not.toHaveBeenCalled();
    });

    it('should handle text layer rendering errors gracefully', async () => {
      const mockPage = createMockPage(1);
      const textLayerDiv = document.createElement('div');

      mockPage.getTextContent = vi.fn().mockRejectedValue(new Error('Text extraction failed'));

      // Should not throw error - text layer is not critical
      await expect(PDFService.renderTextLayer(mockPage, textLayerDiv)).resolves.toBeUndefined();
    });

    it('should clear previous text layer content', async () => {
      const mockPage = createMockPage(1);
      const textLayerDiv = document.createElement('div');

      textLayerDiv.innerHTML = '<div>Previous content</div>';

      await PDFService.renderTextLayer(mockPage, textLayerDiv);

      expect(textLayerDiv.innerHTML).toBe('');
    });
  });

  describe('renderAnnotationLayer', () => {
    it('should successfully render annotation layer', async () => {
      const mockPage = createMockPage(1);
      const annotationLayerDiv = document.createElement('div');
      const scale = 1.0;

      const mockAnnotations = [
        { id: 1, type: 'text', content: 'Test annotation' },
        { id: 2, type: 'highlight', content: 'Highlighted text' },
      ];

      mockPage.getAnnotations = vi.fn().mockResolvedValue(mockAnnotations);

      await PDFService.renderAnnotationLayer(mockPage, annotationLayerDiv, scale);

      expect(mockPage.getAnnotations).toHaveBeenCalled();
      expect(annotationLayerDiv.style.position).toBe('absolute');
      expect(annotationLayerDiv.innerHTML).toBe(''); // Simple implementation for POC
    });

    it('should handle null annotation layer div gracefully', async () => {
      const mockPage = createMockPage(1);

      // Should not throw error
      await expect(
        PDFService.renderAnnotationLayer(mockPage, null as unknown as HTMLDivElement)
      ).resolves.toBeUndefined();

      expect(mockPage.getAnnotations).not.toHaveBeenCalled();
    });

    it('should handle annotation loading errors gracefully', async () => {
      const mockPage = createMockPage(1);
      const annotationLayerDiv = document.createElement('div');

      mockPage.getAnnotations = vi.fn().mockRejectedValue(new Error('Annotation load failed'));

      // Should not throw error - annotation layer is not critical
      await expect(
        PDFService.renderAnnotationLayer(mockPage, annotationLayerDiv)
      ).resolves.toBeUndefined();
    });

    it('should handle pages with no annotations', async () => {
      const mockPage = createMockPage(1);
      const annotationLayerDiv = document.createElement('div');

      mockPage.getAnnotations = vi.fn().mockResolvedValue([]);

      await PDFService.renderAnnotationLayer(mockPage, annotationLayerDiv);

      expect(mockPage.getAnnotations).toHaveBeenCalled();
      expect(annotationLayerDiv.innerHTML).toBe('');
    });
  });

  describe('cleanup', () => {
    it('should cleanup specific document', async () => {
      const mockDocument1 = createMockDocument(5);
      const mockDocument2 = createMockDocument(3);

      const mockLoadingTask1 = { promise: Promise.resolve(mockDocument1) };
      const mockLoadingTask2 = { promise: Promise.resolve(mockDocument2) };

      mockPDFJS.getDocument
        .mockReturnValueOnce(mockLoadingTask1)
        .mockReturnValueOnce(mockLoadingTask2);

      // Load two documents
      await PDFService.loadDocument('doc1.pdf');
      await PDFService.loadDocument('doc2.pdf');

      const loadedDocs = PDFService.getLoadedDocuments();
      expect(loadedDocs.size).toBe(2);

      // Cleanup specific document
      PDFService.cleanup(mockDocument1);

      const remainingDocs = PDFService.getLoadedDocuments();
      expect(remainingDocs.size).toBe(1);
      expect(remainingDocs.has('doc2.pdf')).toBe(true);
    });

    it('should cleanup all documents when no specific document provided', async () => {
      const mockDocument = createMockDocument(5);
      const mockLoadingTask = { promise: Promise.resolve(mockDocument) };

      mockPDFJS.getDocument.mockReturnValue(mockLoadingTask);

      await PDFService.loadDocument('test.pdf');

      const loadedDocs = PDFService.getLoadedDocuments();
      expect(loadedDocs.size).toBe(1);

      PDFService.cleanup();

      const remainingDocs = PDFService.getLoadedDocuments();
      expect(remainingDocs.size).toBe(0);
    });

    it('should handle cleanup of non-existent document', () => {
      const nonExistentDocument = createMockDocument(1);

      // Should not throw error
      expect(() => PDFService.cleanup(nonExistentDocument)).not.toThrow();
    });
  });

  describe('getLoadedDocuments', () => {
    it('should return copy of loaded documents map', async () => {
      const mockDocument = createMockDocument(5);
      const mockLoadingTask = { promise: Promise.resolve(mockDocument) };

      mockPDFJS.getDocument.mockReturnValue(mockLoadingTask);

      await PDFService.loadDocument('test.pdf');

      const loadedDocs = PDFService.getLoadedDocuments();
      expect(loadedDocs).toBeInstanceOf(Map);
      expect(loadedDocs.size).toBe(1);
      expect(loadedDocs.get('test.pdf')).toBe(mockDocument);

      // Verify it's a copy (mutations don't affect internal state)
      loadedDocs.clear();

      const loadedDocsAgain = PDFService.getLoadedDocuments();
      expect(loadedDocsAgain.size).toBe(1); // Should still have the document
    });

    it('should return empty map when no documents loaded', () => {
      const loadedDocs = PDFService.getLoadedDocuments();
      expect(loadedDocs).toBeInstanceOf(Map);
      expect(loadedDocs.size).toBe(0);
    });
  });

  describe('worker configuration', () => {
    it('should set worker source on module load', () => {
      expect(mockPDFJS.GlobalWorkerOptions.workerSrc).toBeDefined();
      expect(mockPDFJS.GlobalWorkerOptions.workerSrc).toContain('pdf.worker');
    });
  });

  describe('error edge cases', () => {
    it('should handle missing viewport in page render', async () => {
      const mockPage = createMockPage(1);
      const canvas = createMockCanvas();

      mockPage.getViewport = vi.fn(() => {
        throw new Error('Viewport error');
      });

      await expect(PDFService.renderPageToCanvas(mockPage, canvas)).rejects.toThrow(
        'Failed to render page'
      );
    });

    it('should clean up render state on error', async () => {
      const mockPage = createMockPage(1);
      const canvas = createMockCanvas();

      mockPage.render = vi.fn(() => createMockRenderTask(true));

      try {
        await PDFService.renderPageToCanvas(mockPage, canvas);
      } catch {
        // Expected to fail
      }

      // Verify cleanup occurred
      expect((canvas as unknown as { _isRendering: boolean })._isRendering).toBe(false);
      expect((canvas as unknown as { _pdfRenderTask: object | null })._pdfRenderTask).toBe(null);
    });

    it('should handle render task cancellation errors', async () => {
      const mockPage = createMockPage(1);
      const canvas = createMockCanvas();

      const existingTask = {
        cancel: vi.fn().mockRejectedValue(new Error('Cancel failed')),
        promise: Promise.resolve(),
      };

      (canvas as unknown as { _pdfRenderTask: object })._pdfRenderTask = existingTask;

      // Should handle cancellation error gracefully
      await expect(PDFService.renderPageToCanvas(mockPage, canvas)).resolves.toBeUndefined();
    });
  });
});
