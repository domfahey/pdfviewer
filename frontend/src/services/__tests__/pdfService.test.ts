/**
 * Comprehensive unit tests for pdfService.
 * 
 * Tests cover PDF document loading, page rendering, cleanup,
 * caching, and error handling.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { PDFService } from '../pdfService';
import * as pdfjsLib from 'pdfjs-dist';
import type { PDFDocumentProxy, PDFPageProxy, PageViewport } from 'pdfjs-dist';

// Mock pdfjs-dist
vi.mock('pdfjs-dist', () => ({
  GlobalWorkerOptions: {
    workerSrc: '',
  },
  getDocument: vi.fn(),
  version: '3.0.0',
  TextLayer: vi.fn(),
}));

describe('PDFService', () => {
  const mockViewport: PageViewport = {
    width: 600,
    height: 800,
    scale: 1.0,
  } as PageViewport;

  const mockPage: Partial<PDFPageProxy> = {
    pageNumber: 1,
    getViewport: vi.fn().mockReturnValue(mockViewport),
    render: vi.fn().mockReturnValue({
      promise: Promise.resolve(),
      cancel: vi.fn(),
    }),
    getTextContent: vi.fn().mockResolvedValue({
      items: [{ str: 'test text' }],
      styles: {},
    }),
    getAnnotations: vi.fn().mockResolvedValue([]),
  };

  const mockDocument: Partial<PDFDocumentProxy> = {
    numPages: 10,
    fingerprints: ['test-fingerprint'],
    getPage: vi.fn().mockResolvedValue(mockPage),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    PDFService.cleanup(); // Clear cache before each test
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('loadDocument', () => {
    it('should successfully load a PDF document', async () => {
      const loadingTask = {
        promise: Promise.resolve(mockDocument as PDFDocumentProxy),
      };

      vi.mocked(pdfjsLib.getDocument).mockReturnValue(loadingTask as any);

      const doc = await PDFService.loadDocument('test.pdf');

      expect(doc).toBe(mockDocument);
      expect(pdfjsLib.getDocument).toHaveBeenCalledWith(
        expect.objectContaining({
          url: 'test.pdf',
          cMapPacked: true,
          enableXfa: true,
        })
      );
    });

    it('should cache loaded documents', async () => {
      const loadingTask = {
        promise: Promise.resolve(mockDocument as PDFDocumentProxy),
      };

      vi.mocked(pdfjsLib.getDocument).mockReturnValue(loadingTask as any);

      // Load document first time
      const doc1 = await PDFService.loadDocument('test.pdf');

      // Load same document again
      const doc2 = await PDFService.loadDocument('test.pdf');

      expect(doc1).toBe(doc2);
      expect(pdfjsLib.getDocument).toHaveBeenCalledTimes(1); // Should only load once
    });

    it('should load different documents separately', async () => {
      const doc1 = { ...mockDocument, fingerprints: ['doc1'] };
      const doc2 = { ...mockDocument, fingerprints: ['doc2'] };

      vi.mocked(pdfjsLib.getDocument)
        .mockReturnValueOnce({
          promise: Promise.resolve(doc1 as PDFDocumentProxy),
        } as any)
        .mockReturnValueOnce({
          promise: Promise.resolve(doc2 as PDFDocumentProxy),
        } as any);

      const result1 = await PDFService.loadDocument('test1.pdf');
      const result2 = await PDFService.loadDocument('test2.pdf');

      expect(result1).toBe(doc1);
      expect(result2).toBe(doc2);
      expect(pdfjsLib.getDocument).toHaveBeenCalledTimes(2);
    });

    it('should handle document load failure', async () => {
      const loadingTask = {
        promise: Promise.reject(new Error('Load failed')),
      };

      vi.mocked(pdfjsLib.getDocument).mockReturnValue(loadingTask as any);

      await expect(PDFService.loadDocument('invalid.pdf')).rejects.toThrow(
        'Failed to load PDF document'
      );
    });

    it('should configure PDF.js with correct options', async () => {
      const loadingTask = {
        promise: Promise.resolve(mockDocument as PDFDocumentProxy),
      };

      vi.mocked(pdfjsLib.getDocument).mockReturnValue(loadingTask as any);

      await PDFService.loadDocument('test.pdf');

      expect(pdfjsLib.getDocument).toHaveBeenCalledWith(
        expect.objectContaining({
          url: 'test.pdf',
          cMapUrl: expect.stringContaining('cmaps'),
          cMapPacked: true,
          enableXfa: true,
        })
      );
    });
  });

  describe('getPage', () => {
    it('should successfully get a page from document', async () => {
      const page = await PDFService.getPage(
        mockDocument as PDFDocumentProxy,
        1
      );

      expect(page).toBe(mockPage);
      expect(mockDocument.getPage).toHaveBeenCalledWith(1);
    });

    it('should handle invalid page number', async () => {
      const errorDoc = {
        ...mockDocument,
        getPage: vi.fn().mockRejectedValue(new Error('Page not found')),
      };

      await expect(
        PDFService.getPage(errorDoc as PDFDocumentProxy, 999)
      ).rejects.toThrow('Failed to load page 999');
    });

    it('should get different pages', async () => {
      const page1 = { ...mockPage, pageNumber: 1 };
      const page2 = { ...mockPage, pageNumber: 2 };

      const doc = {
        ...mockDocument,
        getPage: vi
          .fn()
          .mockResolvedValueOnce(page1)
          .mockResolvedValueOnce(page2),
      };

      const result1 = await PDFService.getPage(doc as PDFDocumentProxy, 1);
      const result2 = await PDFService.getPage(doc as PDFDocumentProxy, 2);

      expect(result1.pageNumber).toBe(1);
      expect(result2.pageNumber).toBe(2);
    });
  });

  describe('renderPageToCanvas', () => {
    let canvas: HTMLCanvasElement;
    let context: CanvasRenderingContext2D;

    beforeEach(() => {
      canvas = document.createElement('canvas');
      context = {
        clearRect: vi.fn(),
      } as unknown as CanvasRenderingContext2D;

      vi.spyOn(canvas, 'getContext').mockReturnValue(context);
    });

    it('should successfully render page to canvas', async () => {
      await PDFService.renderPageToCanvas(
        mockPage as PDFPageProxy,
        canvas,
        1.0
      );

      expect(mockPage.getViewport).toHaveBeenCalledWith({ scale: 1.0 });
      expect(mockPage.render).toHaveBeenCalled();
      expect(canvas.width).toBe(600);
      expect(canvas.height).toBe(800);
    });

    it('should apply custom scale', async () => {
      const scaledViewport = { width: 1200, height: 1600, scale: 2.0 };
      vi.mocked(mockPage.getViewport).mockReturnValue(
        scaledViewport as PageViewport
      );

      await PDFService.renderPageToCanvas(
        mockPage as PDFPageProxy,
        canvas,
        2.0
      );

      expect(mockPage.getViewport).toHaveBeenCalledWith({ scale: 2.0 });
      expect(canvas.width).toBe(1200);
      expect(canvas.height).toBe(1600);
    });

    it('should handle missing canvas context', async () => {
      vi.spyOn(canvas, 'getContext').mockReturnValue(null);

      await expect(
        PDFService.renderPageToCanvas(mockPage as PDFPageProxy, canvas, 1.0)
      ).rejects.toThrow('Failed to get canvas context');
    });

    it('should prevent concurrent renders on same canvas', async () => {
      const renderPromise = PDFService.renderPageToCanvas(
        mockPage as PDFPageProxy,
        canvas,
        1.0
      );

      // Try to render again before first completes
      await PDFService.renderPageToCanvas(
        mockPage as PDFPageProxy,
        canvas,
        1.0
      );

      await renderPromise;

      // Should only render once due to concurrency check
      expect(mockPage.render).toHaveBeenCalledTimes(1);
    });

    it('should cancel existing render task', async () => {
      const cancelMock = vi.fn().mockResolvedValue(undefined);
      const firstRenderTask = {
        promise: new Promise((resolve) => setTimeout(resolve, 100)),
        cancel: cancelMock,
      };

      vi.mocked(mockPage.render).mockReturnValueOnce(firstRenderTask as any);

      // Start first render
      const firstRender = PDFService.renderPageToCanvas(
        mockPage as PDFPageProxy,
        canvas,
        1.0
      );

      // Wait a bit then start second render
      await new Promise((resolve) => setTimeout(resolve, 10));

      // Reset the render mock for second call
      vi.mocked(mockPage.render).mockReturnValue({
        promise: Promise.resolve(),
        cancel: vi.fn(),
      } as any);

      const secondRender = PDFService.renderPageToCanvas(
        mockPage as PDFPageProxy,
        canvas,
        1.0
      );

      await Promise.all([firstRender, secondRender]);

      expect(cancelMock).toHaveBeenCalled();
    });

    it('should handle RenderingCancelledException gracefully', async () => {
      const renderTask = {
        promise: Promise.reject({
          name: 'RenderingCancelledException',
          message: 'Rendering cancelled for page 1',
        }),
        cancel: vi.fn(),
      };

      vi.mocked(mockPage.render).mockReturnValue(renderTask as any);

      // Should not throw error for cancellation
      await expect(
        PDFService.renderPageToCanvas(mockPage as PDFPageProxy, canvas, 1.0)
      ).resolves.toBeUndefined();
    });

    it('should clear canvas before rendering', async () => {
      await PDFService.renderPageToCanvas(
        mockPage as PDFPageProxy,
        canvas,
        1.0
      );

      expect(context.clearRect).toHaveBeenCalledWith(0, 0, 0, 0);
    });
  });

  describe('renderTextLayer', () => {
    let textLayerDiv: HTMLDivElement;

    beforeEach(() => {
      textLayerDiv = document.createElement('div');
    });

    it('should render text layer successfully', async () => {
      const mockTextLayer = {
        render: vi.fn().mockResolvedValue(undefined),
      };

      vi.mocked(pdfjsLib.TextLayer).mockReturnValue(mockTextLayer as any);

      await PDFService.renderTextLayer(
        mockPage as PDFPageProxy,
        textLayerDiv,
        1.0
      );

      expect(mockPage.getTextContent).toHaveBeenCalled();
      expect(mockTextLayer.render).toHaveBeenCalled();
    });

    it('should handle null text layer div', async () => {
      // Should not throw error
      await expect(
        PDFService.renderTextLayer(mockPage as PDFPageProxy, null as any, 1.0)
      ).resolves.toBeUndefined();

      expect(mockPage.getTextContent).not.toHaveBeenCalled();
    });

    it('should clear previous content', async () => {
      textLayerDiv.innerHTML = '<div>Previous content</div>';

      const mockTextLayer = {
        render: vi.fn().mockResolvedValue(undefined),
      };

      vi.mocked(pdfjsLib.TextLayer).mockReturnValue(mockTextLayer as any);

      await PDFService.renderTextLayer(
        mockPage as PDFPageProxy,
        textLayerDiv,
        1.0
      );

      expect(textLayerDiv.innerHTML).not.toContain('Previous content');
    });

    it('should not throw on text layer error', async () => {
      vi.mocked(mockPage.getTextContent).mockRejectedValue(
        new Error('Text extraction failed')
      );

      // Should not throw error
      await expect(
        PDFService.renderTextLayer(mockPage as PDFPageProxy, textLayerDiv, 1.0)
      ).resolves.toBeUndefined();
    });
  });

  describe('renderAnnotationLayer', () => {
    let annotationLayerDiv: HTMLDivElement;

    beforeEach(() => {
      annotationLayerDiv = document.createElement('div');
    });

    it('should render annotation layer successfully', async () => {
      await PDFService.renderAnnotationLayer(
        mockPage as PDFPageProxy,
        annotationLayerDiv,
        1.0
      );

      expect(mockPage.getAnnotations).toHaveBeenCalled();
    });

    it('should handle null annotation layer div', async () => {
      // Should not throw error
      await expect(
        PDFService.renderAnnotationLayer(
          mockPage as PDFPageProxy,
          null as any,
          1.0
        )
      ).resolves.toBeUndefined();

      expect(mockPage.getAnnotations).not.toHaveBeenCalled();
    });

    it('should clear previous content', async () => {
      annotationLayerDiv.innerHTML = '<div>Previous</div>';

      await PDFService.renderAnnotationLayer(
        mockPage as PDFPageProxy,
        annotationLayerDiv,
        1.0
      );

      expect(annotationLayerDiv.innerHTML).toBe('');
    });

    it('should handle annotations present', async () => {
      vi.mocked(mockPage.getAnnotations).mockResolvedValue([
        { subtype: 'Link' },
        { subtype: 'Text' },
      ] as any);

      await PDFService.renderAnnotationLayer(
        mockPage as PDFPageProxy,
        annotationLayerDiv,
        1.0
      );

      expect(mockPage.getAnnotations).toHaveBeenCalled();
    });

    it('should not throw on annotation error', async () => {
      vi.mocked(mockPage.getAnnotations).mockRejectedValue(
        new Error('Annotation error')
      );

      // Should not throw error
      await expect(
        PDFService.renderAnnotationLayer(
          mockPage as PDFPageProxy,
          annotationLayerDiv,
          1.0
        )
      ).resolves.toBeUndefined();
    });
  });

  describe('cleanup', () => {
    it('should cleanup specific document', async () => {
      const loadingTask = {
        promise: Promise.resolve(mockDocument as PDFDocumentProxy),
      };

      vi.mocked(pdfjsLib.getDocument).mockReturnValue(loadingTask as any);

      const doc = await PDFService.loadDocument('test.pdf');

      PDFService.cleanup(doc);

      const loadedDocs = PDFService.getLoadedDocuments();
      expect(loadedDocs.size).toBe(0);
    });

    it('should cleanup all documents', async () => {
      const loadingTask1 = {
        promise: Promise.resolve({
          ...mockDocument,
          fingerprints: ['doc1'],
        } as PDFDocumentProxy),
      };

      const loadingTask2 = {
        promise: Promise.resolve({
          ...mockDocument,
          fingerprints: ['doc2'],
        } as PDFDocumentProxy),
      };

      vi.mocked(pdfjsLib.getDocument)
        .mockReturnValueOnce(loadingTask1 as any)
        .mockReturnValueOnce(loadingTask2 as any);

      await PDFService.loadDocument('test1.pdf');
      await PDFService.loadDocument('test2.pdf');

      PDFService.cleanup();

      const loadedDocs = PDFService.getLoadedDocuments();
      expect(loadedDocs.size).toBe(0);
    });

    it('should handle cleanup with no documents', () => {
      expect(() => PDFService.cleanup()).not.toThrow();

      const loadedDocs = PDFService.getLoadedDocuments();
      expect(loadedDocs.size).toBe(0);
    });
  });

  describe('getLoadedDocuments', () => {
    it('should return copy of loaded documents', async () => {
      const loadingTask = {
        promise: Promise.resolve(mockDocument as PDFDocumentProxy),
      };

      vi.mocked(pdfjsLib.getDocument).mockReturnValue(loadingTask as any);

      await PDFService.loadDocument('test.pdf');

      const loadedDocs = PDFService.getLoadedDocuments();
      expect(loadedDocs.size).toBe(1);
      expect(loadedDocs.has('test.pdf')).toBe(true);

      // Modifying returned map shouldn't affect internal cache
      loadedDocs.clear();
      const loadedDocsAgain = PDFService.getLoadedDocuments();
      expect(loadedDocsAgain.size).toBe(1);
    });
  });
});
