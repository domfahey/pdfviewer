import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import PDFViewer from '../PDFViewer';

// Mock PDF.js
vi.mock('../../services/pdfService', () => ({
  loadPDF: vi.fn(),
  renderPage: vi.fn(),
}));

describe('PDFViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    render(<PDFViewer fileId="test-id" />);
    expect(screen.getByText('Loading PDF...')).toBeInTheDocument();
  });

  it('renders error state when file ID is not provided', () => {
    render(<PDFViewer fileId="" />);
    expect(screen.getByText('No file selected')).toBeInTheDocument();
  });

  it('shows page navigation controls when PDF is loaded', async () => {
    const mockLoadPDF = vi.fn().mockResolvedValue({
      numPages: 5,
      getPage: vi.fn().mockResolvedValue({}),
    });
    
    const mockRenderPage = vi.fn().mockResolvedValue('mock-canvas');
    
    const { loadPDF, renderPage } = await import('../../services/pdfService');
    (loadPDF as any).mockImplementation(mockLoadPDF);
    (renderPage as any).mockImplementation(mockRenderPage);

    render(<PDFViewer fileId="test-id" />);

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
    
    const { loadPDF } = await import('../../services/pdfService');
    (loadPDF as any).mockImplementation(mockLoadPDF);

    render(<PDFViewer fileId="test-id" />);

    await waitFor(() => {
      expect(screen.getByText('Zoom In')).toBeInTheDocument();
      expect(screen.getByText('Zoom Out')).toBeInTheDocument();
      expect(screen.getByText('100%')).toBeInTheDocument();
    });
  });
});