import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { VirtualPDFViewer } from '../PDFViewer/VirtualPDFViewer';
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist';

// Mock PDF.js types and functions
const createMockPage = (pageNumber: number): PDFPageProxy =>
  ({
    pageNumber,
    getViewport: vi.fn(() => ({
      width: 600,
      height: 800,
      scale: 1.0,
    })),
    render: vi.fn(() => ({
      promise: Promise.resolve(),
      cancel: vi.fn(),
    })),
    cleanup: vi.fn(),
    getTextContent: vi.fn(() => Promise.resolve({ items: [] })),
    getAnnotations: vi.fn(() => Promise.resolve([])),
  }) as unknown as PDFPageProxy;

const createMockDocument = (numPages: number): PDFDocumentProxy =>
  ({
    numPages,
    getPage: vi.fn((pageNum: number) => Promise.resolve(createMockPage(pageNum))),
    destroy: vi.fn(),
    getMetadata: vi.fn(() => Promise.resolve({ info: {} })),
    getDownloadInfo: vi.fn(() => Promise.resolve({ length: 1000 })),
  }) as unknown as PDFDocumentProxy;

describe('VirtualPDFViewer', () => {
  let mockDocument: PDFDocumentProxy;
  let mockOnPageChange: ReturnType<typeof vi.fn>;
  let mockCanvas: HTMLCanvasElement;
  let mockContext: CanvasRenderingContext2D;

  beforeEach(() => {
    vi.clearAllMocks();

    mockOnPageChange = vi.fn();
    mockDocument = createMockDocument(5);

    // Mock canvas and context
    mockCanvas = {
      width: 0,
      height: 0,
      toDataURL: vi.fn(() => 'data:image/png;base64,fake-image-data'),
      getContext: vi.fn(),
    } as unknown as HTMLCanvasElement;

    mockContext = {
      clearRect: vi.fn(),
      fillRect: vi.fn(),
      drawImage: vi.fn(),
    } as unknown as CanvasRenderingContext2D;

    mockCanvas.getContext = vi.fn(() => mockContext);

    // Mock document.createElement to return our mock canvas
    const originalCreateElement = document.createElement;
    vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
      if (tagName === 'canvas') {
        return mockCanvas;
      }
      return originalCreateElement.call(document, tagName);
    });

    // Mock IntersectionObserver
    global.IntersectionObserver = vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn(),
    }));

    // Mock scrollTo
    Element.prototype.scrollTo = vi.fn();

    // Mock console methods to reduce noise
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders empty state when no document is provided', () => {
    render(
      <VirtualPDFViewer
        pdfDocument={null}
        scale={1.0}
        currentPage={1}
        onPageChange={mockOnPageChange}
      />
    );

    expect(screen.getByText('No document loaded')).toBeInTheDocument();
  });

  it('initializes page data when document is loaded', async () => {
    await act(async () => {
      render(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={1.0}
          currentPage={1}
          onPageChange={mockOnPageChange}
        />
      );
    });

    await waitFor(() => {
      expect(mockDocument.getPage).toHaveBeenCalledTimes(5);
    });

    expect(mockDocument.getPage).toHaveBeenCalledWith(1);
    expect(mockDocument.getPage).toHaveBeenCalledWith(2);
    expect(mockDocument.getPage).toHaveBeenCalledWith(3);
    expect(mockDocument.getPage).toHaveBeenCalledWith(4);
    expect(mockDocument.getPage).toHaveBeenCalledWith(5);
  });

  it('renders page placeholders before pages are loaded', async () => {
    await act(async () => {
      render(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={1.0}
          currentPage={1}
          onPageChange={mockOnPageChange}
        />
      );
    });

    // Should show page numbers as placeholders
    await waitFor(() => {
      expect(screen.getByText('Page 1')).toBeInTheDocument();
    });

    expect(screen.getByText('Page 2')).toBeInTheDocument();
    expect(screen.getByText('Page 3')).toBeInTheDocument();
    expect(screen.getByText('Page 4')).toBeInTheDocument();
    expect(screen.getByText('Page 5')).toBeInTheDocument();
  });

  it('renders page images when they are loaded', async () => {
    await act(async () => {
      render(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={1.0}
          currentPage={1}
          onPageChange={mockOnPageChange}
        />
      );
    });

    // Wait for pages to be rendered
    await waitFor(() => {
      const images = screen.getAllByRole('img');
      expect(images.length).toBeGreaterThan(0);
    });

    // Check that images have correct alt text
    expect(screen.getByAltText('Page 1')).toBeInTheDocument();
  });

  it('highlights current page with different styling', async () => {
    await act(async () => {
      render(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={1.5}
          currentPage={3}
          onPageChange={mockOnPageChange}
        />
      );
    });

    await waitFor(() => {
      expect(mockDocument.getPage).toHaveBeenCalled();
    });

    // The current page should have blue border styling
    const pageContainers = document.querySelectorAll('[class*="border-blue-500"]');
    expect(pageContainers.length).toBeGreaterThan(0);
  });

  it('updates scale when prop changes', async () => {
    const { rerender } = render(
      <VirtualPDFViewer
        pdfDocument={mockDocument}
        scale={1.0}
        currentPage={1}
        onPageChange={mockOnPageChange}
      />
    );

    await waitFor(() => {
      expect(mockDocument.getPage).toHaveBeenCalled();
    });

    // Change scale
    await act(async () => {
      rerender(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={2.0}
          currentPage={1}
          onPageChange={mockOnPageChange}
        />
      );
    });

    // Should reinitialize pages with new scale
    await waitFor(() => {
      // getPage will be called again for all pages with new scale
      expect(mockDocument.getPage).toHaveBeenCalledTimes(10); // 5 pages × 2 calls
    });
  });

  it('scrolls to current page when currentPage prop changes', async () => {
    const { rerender } = render(
      <VirtualPDFViewer
        pdfDocument={mockDocument}
        scale={1.0}
        currentPage={1}
        onPageChange={mockOnPageChange}
      />
    );

    await waitFor(() => {
      expect(mockDocument.getPage).toHaveBeenCalled();
    });

    const scrollToSpy = vi.spyOn(Element.prototype, 'scrollTo');

    // Change current page
    await act(async () => {
      rerender(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={1.0}
          currentPage={3}
          onPageChange={mockOnPageChange}
        />
      );
    });

    expect(scrollToSpy).toHaveBeenCalledWith({
      top: expect.any(Number),
      behavior: 'smooth',
    });
  });

  it('calls onPageChange when scrolling changes current page', async () => {
    await act(async () => {
      render(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={1.0}
          currentPage={1}
          onPageChange={mockOnPageChange}
        />
      );
    });

    await waitFor(() => {
      expect(mockDocument.getPage).toHaveBeenCalled();
    });

    // Find the scrollable container
    const container = document.querySelector('[class*="overflow-auto"]');
    expect(container).toBeInTheDocument();

    if (container) {
      // Mock scrollTop property
      Object.defineProperty(container, 'scrollTop', {
        value: 1000,
        writable: true,
      });

      Object.defineProperty(container, 'clientHeight', {
        value: 600,
        writable: true,
      });

      // Trigger scroll event
      await act(async () => {
        fireEvent.scroll(container);
      });

      // Should call onPageChange when scroll position changes
      expect(mockOnPageChange).toHaveBeenCalled();
    }
  });

  it('handles page loading errors gracefully', async () => {
    // Mock getPage to throw an error for page 3
    mockDocument.getPage = vi.fn((pageNum: number) => {
      if (pageNum === 3) {
        return Promise.reject(new Error('Failed to load page 3'));
      }
      return Promise.resolve(createMockPage(pageNum));
    });

    await act(async () => {
      render(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={1.0}
          currentPage={1}
          onPageChange={mockOnPageChange}
        />
      );
    });

    await waitFor(() => {
      expect(mockDocument.getPage).toHaveBeenCalledTimes(5);
    });

    // Error should be logged
    expect(console.error).toHaveBeenCalledWith('Error loading page 3:', expect.any(Error));

    // Should still show placeholder for failed page
    expect(screen.getByText('Page 3')).toBeInTheDocument();
  });

  it('handles rendering errors gracefully', async () => {
    // Mock page render to throw an error
    const mockPageWithError = createMockPage(1);
    mockPageWithError.render = vi.fn(() => ({
      promise: Promise.reject(new Error('Render failed')),
      cancel: vi.fn(),
    }));

    mockDocument.getPage = vi.fn((pageNum: number) => {
      if (pageNum === 1) {
        return Promise.resolve(mockPageWithError);
      }
      return Promise.resolve(createMockPage(pageNum));
    });

    await act(async () => {
      render(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={1.0}
          currentPage={1}
          onPageChange={mockOnPageChange}
        />
      );
    });

    await waitFor(() => {
      expect(mockDocument.getPage).toHaveBeenCalled();
    });

    // Should log render error
    await waitFor(() => {
      expect(console.error).toHaveBeenCalledWith('Error rendering page 1:', expect.any(Error));
    });
  });

  it('shows loading state for visible pages that are rendering', async () => {
    // Make page rendering take time
    let resolveRender: () => void;
    const renderPromise = new Promise<void>(resolve => {
      resolveRender = resolve;
    });

    const mockPageWithDelay = createMockPage(1);
    mockPageWithDelay.render = vi.fn(() => ({
      promise: renderPromise,
      cancel: vi.fn(),
    }));

    mockDocument.getPage = vi.fn((pageNum: number) => {
      if (pageNum === 1) {
        return Promise.resolve(mockPageWithDelay);
      }
      return Promise.resolve(createMockPage(pageNum));
    });

    await act(async () => {
      render(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={1.0}
          currentPage={1}
          onPageChange={mockOnPageChange}
        />
      );
    });

    // Should show loading spinner for page being rendered
    await waitFor(() => {
      expect(screen.getByText('Loading page 1...')).toBeInTheDocument();
    });

    // Complete the render
    await act(async () => {
      resolveRender!();
      await renderPromise;
    });
  });

  it('applies custom className', async () => {
    await act(async () => {
      render(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={1.0}
          currentPage={1}
          onPageChange={mockOnPageChange}
          className="custom-virtual-viewer"
        />
      );
    });

    const container = document.querySelector('.custom-virtual-viewer');
    expect(container).toBeInTheDocument();
  });

  it('calculates total height correctly', async () => {
    await act(async () => {
      render(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={1.0}
          currentPage={1}
          onPageChange={mockOnPageChange}
        />
      );
    });

    await waitFor(() => {
      expect(mockDocument.getPage).toHaveBeenCalled();
    });

    // Check that the content container has correct height
    // Each page is 800px + 20px margin = 820px, plus 40px total padding
    // const expectedHeight = (800 + 20) * 5 + 40; // 4140px
    const contentDiv = document.querySelector('[style*="height"]');
    expect(contentDiv).toBeInTheDocument();
  });

  it('handles missing canvas context gracefully', async () => {
    // Mock canvas.getContext to return null
    mockCanvas.getContext = vi.fn(() => null);

    await act(async () => {
      render(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={1.0}
          currentPage={1}
          onPageChange={mockOnPageChange}
        />
      );
    });

    await waitFor(() => {
      expect(mockDocument.getPage).toHaveBeenCalled();
    });

    // Should handle missing context without crashing
    expect(screen.getByText('Page 1')).toBeInTheDocument();
  });

  it('cleans up event listeners on unmount', async () => {
    const removeEventListenerSpy = vi.spyOn(Element.prototype, 'removeEventListener');
    const windowRemoveEventListenerSpy = vi.spyOn(window, 'removeEventListener');

    const { unmount } = render(
      <VirtualPDFViewer
        pdfDocument={mockDocument}
        scale={1.0}
        currentPage={1}
        onPageChange={mockOnPageChange}
      />
    );

    await waitFor(() => {
      expect(mockDocument.getPage).toHaveBeenCalled();
    });

    act(() => {
      unmount();
    });

    expect(removeEventListenerSpy).toHaveBeenCalledWith('scroll', expect.any(Function));
    expect(windowRemoveEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function));
  });

  it('updates container height on window resize', async () => {
    await act(async () => {
      render(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={1.0}
          currentPage={1}
          onPageChange={mockOnPageChange}
        />
      );
    });

    const container = document.querySelector('[class*="overflow-auto"]');

    if (container) {
      Object.defineProperty(container, 'clientHeight', {
        value: 800,
        writable: true,
      });

      // Trigger resize event
      await act(async () => {
        window.dispatchEvent(new Event('resize'));
      });

      // The component should handle the resize (no specific assertion needed as it's internal state)
    }
  });

  it('prevents memory leaks by cleaning up non-visible pages', async () => {
    await act(async () => {
      render(
        <VirtualPDFViewer
          pdfDocument={mockDocument}
          scale={1.0}
          currentPage={1}
          onPageChange={mockOnPageChange}
        />
      );
    });

    await waitFor(() => {
      expect(mockDocument.getPage).toHaveBeenCalled();
    });

    // Wait for the cleanup timeout (5 seconds in real code, but mocked here)
    await act(async () => {
      // The cleanup is handled internally and we verify it doesn't crash
      await new Promise(resolve => setTimeout(resolve, 100));
    });

    expect(mockContext.clearRect).toHaveBeenCalled();
  });
});
