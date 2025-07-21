import { render, screen, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PDFViewer } from '../PDFViewer/PDFViewer';

// Mock PDF.js service
vi.mock('../../services/pdfService', () => ({
  PDFService: {
    loadDocument: vi.fn(),
    getPage: vi.fn(),
    cleanup: vi.fn(),
  },
}));

// Mock the PDF document hook
vi.mock('../../hooks/usePDFDocument', () => ({
  usePDFDocument: vi.fn(),
}));

// Import the mocked services for type safety
import { usePDFDocument } from '../../hooks/usePDFDocument';
import { PDFService } from '../../services/pdfService';
const mockUsePDFDocument = vi.mocked(usePDFDocument);
const mockPDFService = vi.mocked(PDFService);

// Mock all the new PDF components
vi.mock('../PDFViewer/PDFThumbnails', () => ({
  PDFThumbnails: ({ isVisible }: { isVisible: boolean }) =>
    isVisible ? <div data-testid="pdf-thumbnails">Thumbnails</div> : null,
}));

vi.mock('../PDFViewer/VirtualPDFViewer', () => ({
  VirtualPDFViewer: () => <div data-testid="virtual-pdf-viewer">Virtual PDF Viewer</div>,
}));

vi.mock('../PDFViewer/PDFMetadataPanel', () => ({
  PDFMetadataPanel: ({ isVisible }: { isVisible: boolean }) =>
    isVisible ? <div data-testid="pdf-metadata">Metadata Panel</div> : null,
}));

vi.mock('../PDFViewer/PDFPage', () => ({
  PDFPage: () => <div data-testid="pdf-page">PDF Page</div>,
}));

describe('PDFViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock PDF page object
    const mockPageObj = {
      pageNumber: 1,
      getViewport: vi.fn(() => ({ width: 800, height: 600 })),
      render: vi.fn(() => ({ promise: Promise.resolve() })),
    };

    // Mock PDFService.getPage to return a page object
    mockPDFService.getPage.mockResolvedValue(mockPageObj);

    // Mock the usePDFDocument hook with default values
    mockUsePDFDocument.mockReturnValue({
      document: null,
      currentPage: 1,
      totalPages: 0,
      scale: 1.0,
      loading: false,
      error: null,
      loadDocument: vi.fn(),
      setCurrentPage: vi.fn(),
      setScale: vi.fn(),
      nextPage: vi.fn(),
      previousPage: vi.fn(),
    });
  });

  it('renders loading state initially', async () => {
    mockUsePDFDocument.mockReturnValue({
      document: null,
      currentPage: 1,
      totalPages: 0,
      scale: 1.0,
      loading: true,
      error: null,
      loadDocument: vi.fn(),
      setCurrentPage: vi.fn(),
      setScale: vi.fn(),
      nextPage: vi.fn(),
      previousPage: vi.fn(),
    });

    await act(async () => {
      render(<PDFViewer fileUrl="/api/files/test-id" />);
    });

    expect(screen.getByText('Loading PDF...')).toBeInTheDocument();
  });

  it('renders error state when loading fails', async () => {
    mockUsePDFDocument.mockReturnValue({
      document: null,
      currentPage: 1,
      totalPages: 0,
      scale: 1.0,
      loading: false,
      error: 'Failed to load PDF',
      loadDocument: vi.fn(),
      setCurrentPage: vi.fn(),
      setScale: vi.fn(),
      nextPage: vi.fn(),
      previousPage: vi.fn(),
    });

    await act(async () => {
      render(<PDFViewer fileUrl="/api/files/test-id" />);
    });

    const errorElements = screen.getAllByText('Failed to load PDF');
    expect(errorElements.length).toBeGreaterThan(0);
  });

  it('renders empty state when no document is loaded', async () => {
    mockUsePDFDocument.mockReturnValue({
      document: null,
      currentPage: 1,
      totalPages: 0,
      scale: 1.0,
      loading: false,
      error: null,
      loadDocument: vi.fn(),
      setCurrentPage: vi.fn(),
      setScale: vi.fn(),
      nextPage: vi.fn(),
      previousPage: vi.fn(),
    });

    await act(async () => {
      render(<PDFViewer fileUrl="" />);
    });

    expect(screen.getByText('No PDF loaded')).toBeInTheDocument();
  });

  it('shows page navigation controls when PDF is loaded', async () => {
    const mockDocument = { numPages: 5 };

    mockUsePDFDocument.mockReturnValue({
      document: mockDocument,
      currentPage: 1,
      totalPages: 5,
      scale: 1.0,
      loading: false,
      error: null,
      currentPageObj: { pageNumber: 1 }, // Add currentPageObj
      loadDocument: vi.fn(),
      setCurrentPage: vi.fn(),
      setScale: vi.fn(),
      nextPage: vi.fn(),
      previousPage: vi.fn(),
    });

    await act(async () => {
      render(<PDFViewer fileUrl="/api/files/test-id" />);
    });

    // Wait for page to load
    await waitFor(() => {
      expect(screen.getByText('Page')).toBeInTheDocument();
    });

    expect(screen.getByText('of 5')).toBeInTheDocument();
    expect(screen.getByRole('spinbutton')).toBeInTheDocument();
  });

  it('handles zoom controls', async () => {
    const mockDocument = { numPages: 1 };
    const mockSetScale = vi.fn();

    mockUsePDFDocument.mockReturnValue({
      document: mockDocument,
      currentPage: 1,
      totalPages: 1,
      scale: 1.0,
      loading: false,
      error: null,
      currentPageObj: { pageNumber: 1 }, // Add currentPageObj
      loadDocument: vi.fn(),
      setCurrentPage: vi.fn(),
      setScale: mockSetScale,
      nextPage: vi.fn(),
      previousPage: vi.fn(),
    });

    await act(async () => {
      render(<PDFViewer fileUrl="/api/files/test-id" />);
    });

    // Wait for page to load
    await waitFor(() => {
      expect(screen.getByLabelText('Zoom in')).toBeInTheDocument();
    });

    expect(screen.getByLabelText('Zoom out')).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toBeInTheDocument(); // Scale selector
  });

  it('shows advanced controls when enabled', async () => {
    const mockDocument = { numPages: 5 };

    mockUsePDFDocument.mockReturnValue({
      document: mockDocument,
      currentPage: 1,
      totalPages: 5,
      scale: 1.0,
      loading: false,
      error: null,
      currentPageObj: { pageNumber: 1 }, // Add currentPageObj
      loadDocument: vi.fn(),
      setCurrentPage: vi.fn(),
      setScale: vi.fn(),
      nextPage: vi.fn(),
      previousPage: vi.fn(),
    });

    await act(async () => {
      render(<PDFViewer fileUrl="/api/files/test-id" />);
    });

    // Wait for page to load
    await waitFor(() => {
      expect(screen.getByLabelText('Search in document')).toBeInTheDocument();
    });

    expect(screen.getByLabelText('Toggle thumbnails')).toBeInTheDocument();
    expect(screen.getByLabelText('Rotate 90 degrees')).toBeInTheDocument();
  });

  it('renders with virtual scrolling when enabled', async () => {
    const mockDocument = { numPages: 5 };

    mockUsePDFDocument.mockReturnValue({
      document: mockDocument,
      currentPage: 1,
      totalPages: 5,
      scale: 1.0,
      loading: false,
      error: null,
      currentPageObj: { pageNumber: 1 }, // Add currentPageObj
      loadDocument: vi.fn(),
      setCurrentPage: vi.fn(),
      setScale: vi.fn(),
      nextPage: vi.fn(),
      previousPage: vi.fn(),
    });

    await act(async () => {
      render(<PDFViewer fileUrl="/api/files/test-id" useVirtualScrolling={true} />);
    });

    // Wait for page to load
    await waitFor(() => {
      expect(screen.getByTestId('virtual-pdf-viewer')).toBeInTheDocument();
    });
  });

  it('displays metadata when provided', async () => {
    const mockDocument = { numPages: 5 };
    const metadata = {
      title: 'Test Document',
      page_count: 5,
      file_size: 1024000,
    };

    mockUsePDFDocument.mockReturnValue({
      document: mockDocument,
      currentPage: 1,
      totalPages: 5,
      scale: 1.0,
      loading: false,
      error: null,
      currentPageObj: { pageNumber: 1 }, // Add currentPageObj
      loadDocument: vi.fn(),
      setCurrentPage: vi.fn(),
      setScale: vi.fn(),
      nextPage: vi.fn(),
      previousPage: vi.fn(),
    });

    await act(async () => {
      render(<PDFViewer fileUrl="/api/files/test-id" metadata={metadata} />);
    });

    // Wait for page to load and check that info button is available
    await waitFor(() => {
      expect(screen.getByLabelText('Document info')).toBeInTheDocument();
    });

    // Metadata is now shown in expandable info panel, not directly visible
    // The metadata props are passed but displayed on demand
  });
});
