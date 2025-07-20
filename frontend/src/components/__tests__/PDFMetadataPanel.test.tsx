import { render, screen, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PDFMetadataPanel } from '../PDFViewer/PDFMetadataPanel';
import type { PDFDocumentProxy } from 'pdfjs-dist';

// Mock PDF.js
const mockPDFDocument = {
  numPages: 5,
  getMetadata: vi.fn(),
} as unknown as PDFDocumentProxy;

describe('PDFMetadataPanel', () => {
  const defaultFileMetadata = {
    filename: 'test-document.pdf',
    file_size: 1024000,
    upload_time: '2023-01-01T00:00:00Z',
    mime_type: 'application/pdf',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockPDFDocument.getMetadata.mockResolvedValue({
      info: {
        Title: 'Test Document',
        Author: 'Test Author',
        Subject: 'Test Subject',
        Creator: 'Test Creator',
        Producer: 'Test Producer',
        CreationDate: 'D:20230101000000Z',
        ModDate: 'D:20230102000000Z',
      },
    });
  });

  it('renders nothing when not visible', () => {
    const { container } = render(
      <PDFMetadataPanel pdfDocument={null} fileMetadata={defaultFileMetadata} isVisible={false} />
    );

    expect(container.firstChild).toBeNull();
  });

  it('shows loading state initially', async () => {
    // Mock a slow getMetadata call to catch loading state
    mockPDFDocument.getMetadata.mockReturnValue(
      new Promise(resolve =>
        setTimeout(
          () =>
            resolve({
              info: {
                Title: 'Test Document',
                Author: 'Test Author',
              },
            }),
          100
        )
      )
    );

    render(
      <PDFMetadataPanel
        pdfDocument={mockPDFDocument}
        fileMetadata={defaultFileMetadata}
        isVisible={true}
      />
    );

    // Check for loading state immediately after render
    expect(screen.getByText('Loading metadata...')).toBeInTheDocument();

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.getByText('Document Information')).toBeInTheDocument();
      },
      { timeout: 2000 }
    );
  });

  it('displays file information when metadata is loaded', async () => {
    await act(async () => {
      render(
        <PDFMetadataPanel
          pdfDocument={mockPDFDocument}
          fileMetadata={defaultFileMetadata}
          isVisible={true}
        />
      );
    });

    await waitFor(() => {
      expect(screen.getByText('Document Information')).toBeInTheDocument();
    });

    expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
    expect(screen.getByText('1000 KB')).toBeInTheDocument();
    // Check for page count in the context of pages section\n    const pageElements = screen.getAllByText('5');\n    expect(pageElements.length).toBeGreaterThan(0); // Should appear at least once
  });

  it('displays document properties when available', async () => {
    render(
      <PDFMetadataPanel
        pdfDocument={mockPDFDocument}
        fileMetadata={defaultFileMetadata}
        isVisible={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Test Document')).toBeInTheDocument();
    });

    expect(screen.getByText('Test Author')).toBeInTheDocument();
    expect(screen.getByText('Test Subject')).toBeInTheDocument();
    expect(screen.getByText('Test Creator')).toBeInTheDocument();
    expect(screen.getByText('Test Producer')).toBeInTheDocument();
  });

  it('shows security information', async () => {
    render(
      <PDFMetadataPanel
        pdfDocument={mockPDFDocument}
        fileMetadata={defaultFileMetadata}
        isVisible={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Security')).toBeInTheDocument();
    });

    expect(screen.getByText('Not encrypted')).toBeInTheDocument();
  });

  it('shows performance metrics', async () => {
    render(
      <PDFMetadataPanel
        pdfDocument={mockPDFDocument}
        fileMetadata={defaultFileMetadata}
        isVisible={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Performance')).toBeInTheDocument();
    });

    expect(screen.getByText('Pages per MB:')).toBeInTheDocument();
    expect(screen.getByText('Avg. page size:')).toBeInTheDocument();
  });

  it('handles missing document properties gracefully', async () => {
    mockPDFDocument.getMetadata.mockResolvedValue({
      info: {},
    });

    render(
      <PDFMetadataPanel
        pdfDocument={mockPDFDocument}
        fileMetadata={defaultFileMetadata}
        isVisible={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Document Information')).toBeInTheDocument();
    });

    // Should still show file information even without document properties
    expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
    // Check for page count in the context of pages section\n    const pageElements = screen.getAllByText('5');\n    expect(pageElements.length).toBeGreaterThan(0); // Should appear at least once
  });

  it('shows error state when metadata extraction fails', async () => {
    mockPDFDocument.getMetadata.mockRejectedValue(new Error('Failed to load'));

    await act(async () => {
      render(
        <PDFMetadataPanel
          pdfDocument={mockPDFDocument}
          fileMetadata={defaultFileMetadata}
          isVisible={true}
        />
      );
    });

    await waitFor(() => {
      expect(screen.getByText('Failed to extract PDF metadata')).toBeInTheDocument();
    });
  });

  it('formats file sizes correctly', async () => {
    const largeFileMetadata = {
      ...defaultFileMetadata,
      file_size: 1024 * 1024 * 10, // 10 MB
    };

    render(
      <PDFMetadataPanel
        pdfDocument={mockPDFDocument}
        fileMetadata={largeFileMetadata}
        isVisible={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('10 MB')).toBeInTheDocument();
    });
  });

  it('handles malformed dates gracefully', async () => {
    mockPDFDocument.getMetadata.mockResolvedValue({
      info: {
        Title: 'Test Document',
        CreationDate: 'invalid-date',
        ModDate: 'also-invalid',
      },
    });

    render(
      <PDFMetadataPanel
        pdfDocument={mockPDFDocument}
        fileMetadata={defaultFileMetadata}
        isVisible={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Test Document')).toBeInTheDocument();
    });

    // The component will still show the dates section because it creates Date objects
    // but the Date constructor for invalid strings creates 'Invalid Date'
    // Since creationDate and modificationDate are set (even if invalid), the dates section shows
    expect(screen.getByText('Dates')).toBeInTheDocument();
    const invalidDateElements = screen.getAllByText('Invalid Date Invalid Date');
    expect(invalidDateElements.length).toBeGreaterThan(0);
  });
});
