import { render, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { PDFPage } from '../PDFViewer/PDFPage';
import type { PDFPageProxy, RenderTask } from 'pdfjs-dist';

// Extended canvas interface for testing
interface ExtendedHTMLCanvasElement extends HTMLCanvasElement {
  _isRendering?: boolean;
  _pdfRenderTask?: RenderTask | null;
}

// Mock the PDFService
vi.mock('../../services/pdfService', () => ({
  PDFService: {
    renderPageToCanvas: vi.fn(),
    renderTextLayer: vi.fn(),
    renderAnnotationLayer: vi.fn(),
  },
}));

// Import the mocked service for type safety
import { PDFService } from '../../services/pdfService';
const mockPDFService = vi.mocked(PDFService);

describe('PDFPage', () => {
  let mockPage: PDFPageProxy;
  let mockOnPageRender: ReturnType<typeof vi.fn>;
  let mockOnPageError: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();

    // Create mock PDFPageProxy
    mockPage = {
      pageNumber: 1,
      getViewport: vi.fn(() => ({
        width: 800,
        height: 600,
        scale: 1.0,
        rotation: 0,
        transform: [1, 0, 0, 1, 0, 0],
      })),
      render: vi.fn(() => ({ promise: Promise.resolve() })),
      getTextContent: vi.fn(() => Promise.resolve({ items: [] })),
      getAnnotations: vi.fn(() => Promise.resolve([])),
      cleanup: vi.fn(),
    } as unknown as PDFPageProxy;

    mockOnPageRender = vi.fn();
    mockOnPageError = vi.fn();

    // Reset PDF service mocks to resolve successfully by default
    mockPDFService.renderPageToCanvas.mockResolvedValue(undefined);
    mockPDFService.renderTextLayer.mockResolvedValue(undefined);
    mockPDFService.renderAnnotationLayer.mockResolvedValue(undefined);

    // Mock console methods to avoid noise in tests
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the page structure with all layers', async () => {
    await act(async () => {
      render(
        <PDFPage
          page={mockPage}
          scale={1.0}
          onPageRender={mockOnPageRender}
          onPageError={mockOnPageError}
        />
      );
    });

    // Check that all layer elements are present
    const canvas = document.querySelector('canvas');
    expect(canvas).toBeInTheDocument();

    const textLayer = document.querySelector('div[style*="user-select: text"]');
    expect(textLayer).toBeInTheDocument();

    const annotationLayer = document.querySelector('div[style*="pointer-events: auto"]');
    expect(annotationLayer).toBeInTheDocument();
  });

  it('calls PDFService to render canvas layer', async () => {
    await act(async () => {
      render(
        <PDFPage
          page={mockPage}
          scale={1.5}
          onPageRender={mockOnPageRender}
          onPageError={mockOnPageError}
        />
      );
    });

    await waitFor(() => {
      expect(mockPDFService.renderPageToCanvas).toHaveBeenCalledWith(
        mockPage,
        expect.any(HTMLCanvasElement),
        1.5
      );
    });
  });

  it('calls PDFService to render text layer', async () => {
    await act(async () => {
      render(
        <PDFPage
          page={mockPage}
          scale={1.0}
          onPageRender={mockOnPageRender}
          onPageError={mockOnPageError}
        />
      );
    });

    await waitFor(() => {
      expect(mockPDFService.renderTextLayer).toHaveBeenCalledWith(
        mockPage,
        expect.any(HTMLDivElement),
        1.0
      );
    });
  });

  it('calls PDFService to render annotation layer', async () => {
    await act(async () => {
      render(
        <PDFPage
          page={mockPage}
          scale={2.0}
          onPageRender={mockOnPageRender}
          onPageError={mockOnPageError}
        />
      );
    });

    await waitFor(() => {
      expect(mockPDFService.renderAnnotationLayer).toHaveBeenCalledWith(
        mockPage,
        expect.any(HTMLDivElement),
        2.0
      );
    });
  });

  it('calls onPageRender callback when rendering succeeds', async () => {
    await act(async () => {
      render(
        <PDFPage
          page={mockPage}
          scale={1.0}
          onPageRender={mockOnPageRender}
          onPageError={mockOnPageError}
        />
      );
    });

    await waitFor(() => {
      expect(mockOnPageRender).toHaveBeenCalled();
    });
    expect(mockOnPageError).not.toHaveBeenCalled();
  });

  it('calls onPageError callback when canvas rendering fails', async () => {
    const testError = new Error('Canvas rendering failed');
    mockPDFService.renderPageToCanvas.mockRejectedValue(testError);

    await act(async () => {
      render(
        <PDFPage
          page={mockPage}
          scale={1.0}
          onPageRender={mockOnPageRender}
          onPageError={mockOnPageError}
        />
      );
    });

    await waitFor(() => {
      expect(mockOnPageError).toHaveBeenCalledWith('Canvas rendering failed');
    });
    expect(mockOnPageRender).not.toHaveBeenCalled();
  });

  it('calls onPageError callback when text layer rendering fails', async () => {
    const testError = new Error('Text layer rendering failed');
    mockPDFService.renderTextLayer.mockRejectedValue(testError);

    await act(async () => {
      render(
        <PDFPage
          page={mockPage}
          scale={1.0}
          onPageRender={mockOnPageRender}
          onPageError={mockOnPageError}
        />
      );
    });

    await waitFor(() => {
      expect(mockOnPageError).toHaveBeenCalledWith('Text layer rendering failed');
    });
  });

  it('calls onPageError callback when annotation layer rendering fails', async () => {
    const testError = new Error('Annotation layer rendering failed');
    mockPDFService.renderAnnotationLayer.mockRejectedValue(testError);

    await act(async () => {
      render(
        <PDFPage
          page={mockPage}
          scale={1.0}
          onPageRender={mockOnPageRender}
          onPageError={mockOnPageError}
        />
      );
    });

    await waitFor(() => {
      expect(mockOnPageError).toHaveBeenCalledWith('Annotation layer rendering failed');
    });
  });

  it('handles non-Error exceptions properly', async () => {
    mockPDFService.renderPageToCanvas.mockRejectedValue('String error');

    await act(async () => {
      render(
        <PDFPage
          page={mockPage}
          scale={1.0}
          onPageRender={mockOnPageRender}
          onPageError={mockOnPageError}
        />
      );
    });

    await waitFor(() => {
      expect(mockOnPageError).toHaveBeenCalledWith('Failed to render page');
    });
  });

  it('re-renders when scale changes', async () => {
    const { rerender } = render(
      <PDFPage
        page={mockPage}
        scale={1.0}
        onPageRender={mockOnPageRender}
        onPageError={mockOnPageError}
      />
    );

    await waitFor(() => {
      expect(mockPDFService.renderPageToCanvas).toHaveBeenCalledWith(
        mockPage,
        expect.any(HTMLCanvasElement),
        1.0
      );
    });

    // Clear mocks before rerender
    mockPDFService.renderPageToCanvas.mockClear();

    await act(async () => {
      rerender(
        <PDFPage
          page={mockPage}
          scale={2.0}
          onPageRender={mockOnPageRender}
          onPageError={mockOnPageError}
        />
      );
    });

    await waitFor(() => {
      expect(mockPDFService.renderPageToCanvas).toHaveBeenCalledWith(
        mockPage,
        expect.any(HTMLCanvasElement),
        2.0
      );
    });
  });

  it('re-renders when page changes', async () => {
    const { rerender } = render(
      <PDFPage
        page={mockPage}
        scale={1.0}
        onPageRender={mockOnPageRender}
        onPageError={mockOnPageError}
      />
    );

    await waitFor(() => {
      expect(mockPDFService.renderPageToCanvas).toHaveBeenCalledWith(
        mockPage,
        expect.any(HTMLCanvasElement),
        1.0
      );
    });

    // Create a different page
    const newMockPage = {
      ...mockPage,
      pageNumber: 2,
    } as PDFPageProxy;

    // Clear mocks before rerender
    mockPDFService.renderPageToCanvas.mockClear();

    await act(async () => {
      rerender(
        <PDFPage
          page={newMockPage}
          scale={1.0}
          onPageRender={mockOnPageRender}
          onPageError={mockOnPageError}
        />
      );
    });

    await waitFor(() => {
      expect(mockPDFService.renderPageToCanvas).toHaveBeenCalledWith(
        newMockPage,
        expect.any(HTMLCanvasElement),
        1.0
      );
    });
  });

  it('applies custom className', async () => {
    await act(async () => {
      render(
        <PDFPage
          page={mockPage}
          scale={1.0}
          className="custom-pdf-page"
          onPageRender={mockOnPageRender}
          onPageError={mockOnPageError}
        />
      );
    });

    const container = document.querySelector('.custom-pdf-page');
    expect(container).toBeInTheDocument();
  });

  it('works without optional callbacks', async () => {
    await act(async () => {
      render(<PDFPage page={mockPage} scale={1.0} />);
    });

    await waitFor(() => {
      expect(mockPDFService.renderPageToCanvas).toHaveBeenCalled();
    });

    // Should not throw errors even without callbacks
    expect(mockPDFService.renderTextLayer).toHaveBeenCalled();
    expect(mockPDFService.renderAnnotationLayer).toHaveBeenCalled();
  });

  it('cleans up canvas on unmount', async () => {
    const { unmount } = render(
      <PDFPage
        page={mockPage}
        scale={1.0}
        onPageRender={mockOnPageRender}
        onPageError={mockOnPageError}
      />
    );

    // Wait for initial render
    await waitFor(() => {
      expect(mockPDFService.renderPageToCanvas).toHaveBeenCalled();
    });

    const canvas = document.querySelector('canvas');
    const mockClearRect = vi.fn();
    const mockGetContext = vi.fn(() => ({ clearRect: mockClearRect }));
    
    if (canvas) {
      canvas.getContext = mockGetContext;
    }

    act(() => {
      unmount();
    });

    // Verify cleanup was attempted
    expect(mockGetContext).toHaveBeenCalledWith('2d');
    expect(mockClearRect).toHaveBeenCalled();
  });

  it('cancels render task on unmount', async () => {
    const { unmount } = render(
      <PDFPage
        page={mockPage}
        scale={1.0}
        onPageRender={mockOnPageRender}
        onPageError={mockOnPageError}
      />
    );

    // Wait for initial render
    await waitFor(() => {
      expect(mockPDFService.renderPageToCanvas).toHaveBeenCalled();
    });

    const canvas = document.querySelector('canvas');
    const mockCancel = vi.fn();
    
    if (canvas) {
      // Simulate an active render task
      const extendedCanvas = canvas as ExtendedHTMLCanvasElement;
      extendedCanvas._pdfRenderTask = { cancel: mockCancel } as RenderTask;
      extendedCanvas._isRendering = true;
    }

    act(() => {
      unmount();
    });

    // Verify render task was cancelled
    expect(mockCancel).toHaveBeenCalled();
    const extendedCanvas = canvas as ExtendedHTMLCanvasElement | null;
    expect(extendedCanvas?._pdfRenderTask).toBeNull();
    expect(extendedCanvas?._isRendering).toBe(false);
  });

  it('skips render when component is unmounted during async operations', async () => {
    // Make canvas rendering take time
    let resolveRender: () => void;
    const renderPromise = new Promise<void>((resolve) => {
      resolveRender = resolve;
    });
    mockPDFService.renderPageToCanvas.mockReturnValue(renderPromise);

    const { unmount } = render(
      <PDFPage
        page={mockPage}
        scale={1.0}
        onPageRender={mockOnPageRender}
        onPageError={mockOnPageError}
      />
    );

    // Unmount before render completes
    act(() => {
      unmount();
    });

    // Complete the render
    await act(async () => {
      resolveRender!();
      await renderPromise;
    });

    // Callbacks should not be called since component was unmounted
    expect(mockOnPageRender).not.toHaveBeenCalled();
    expect(mockOnPageError).not.toHaveBeenCalled();
  });
});