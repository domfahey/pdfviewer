import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { PDFViewer } from '../PDFViewer/PDFViewer';

// Mock PDF.js
vi.mock('../../services/pdfService', () => ({
  PDFService: {
    loadDocument: vi.fn(),
    getPage: vi.fn(),
    cleanup: vi.fn(),
  },
}));

describe('PDFViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    render(<PDFViewer fileUrl="/api/files/test-id" />);
    expect(screen.getByText('Loading PDF...')).toBeInTheDocument();
  });

  it('renders error state when file ID is not provided', () => {
    render(<PDFViewer fileUrl="" />);
    expect(screen.getByText('No file selected')).toBeInTheDocument();
  });

  it('shows page navigation controls when PDF is loaded', async () => {
    const mockLoadPDF = vi.fn().mockResolvedValue({
      numPages: 5,
      getPage: vi.fn().mockResolvedValue({}),
    });

    const mockRenderPage = vi.fn().mockResolvedValue('mock-canvas');

    const { PDFService } = await import('../../services/pdfService');
    (PDFService.loadDocument as Mock).mockImplementation(mockLoadPDF);
    (PDFService.getPage as Mock).mockImplementation(mockRenderPage);

    render(<PDFViewer fileUrl="/api/files/test-id" />);

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 5')).toBeInTheDocument();
    });

    expect(screen.getByText('Previous')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
  });

  it('handles zoom controls', async () => {
    const mockLoadPDF = vi.fn().mockResolvedValue({
      numPages: 1,
      getPage: vi.fn().mockResolvedValue({}),
    });

    const { PDFService } = await import('../../services/pdfService');
    (PDFService.loadDocument as Mock).mockImplementation(mockLoadPDF);

    render(<PDFViewer fileUrl="/api/files/test-id" />);

    await waitFor(() => {
      expect(screen.getByText('Zoom In')).toBeInTheDocument();
      expect(screen.getByText('Zoom Out')).toBeInTheDocument();
      expect(screen.getByText('100%')).toBeInTheDocument();
    });
  });
});
