import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FileUpload } from '../Upload/FileUpload';

// Mock the upload API
const mockOnUploadSuccess = vi.fn();

describe('FileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('renders upload interface', () => {
    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);

    expect(screen.getByText('Drop your PDF here')).toBeInTheDocument();
    expect(screen.getByText('or click to browse files')).toBeInTheDocument();
    expect(screen.getByText('Maximum file size: 50MB')).toBeInTheDocument();
  });

  it('handles file selection', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          file_id: 'test-id',
          filename: 'test.pdf',
          file_size: 1000,
        }),
    });
    global.fetch = mockFetch;

    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);

    const fileInput = screen.getByRole('button');
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    // Since the input is hidden, we need to trigger the file selection differently
    const hiddenInput = fileInput.querySelector('input[type="file"]') as HTMLInputElement;
    if (hiddenInput) {
      fireEvent.change(hiddenInput, { target: { files: [file] } });
    }

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/upload', expect.any(Object));
    });
  });

  it('shows error for non-PDF files', () => {
    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);

    const fileInput = screen.getByRole('button');
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });

    const hiddenInput = fileInput.querySelector('input[type="file"]') as HTMLInputElement;
    if (hiddenInput) {
      fireEvent.change(hiddenInput, { target: { files: [file] } });
    }

    expect(screen.getByText('Invalid file type')).toBeInTheDocument();
  });

  it('shows error for files too large', () => {
    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);

    const fileInput = screen.getByRole('button');
    const largeFile = new File(['x'.repeat(51 * 1024 * 1024)], 'large.pdf', {
      type: 'application/pdf',
    });

    Object.defineProperty(largeFile, 'size', { value: 51 * 1024 * 1024 });

    const hiddenInput = fileInput.querySelector('input[type="file"]') as HTMLInputElement;
    if (hiddenInput) {
      fireEvent.change(hiddenInput, { target: { files: [largeFile] } });
    }

    expect(screen.getByText('File too large')).toBeInTheDocument();
  });

  it('handles upload progress', async () => {
    const mockFetch = vi.fn().mockImplementation(
      () =>
        new Promise(resolve => {
          setTimeout(() => {
            resolve({
              ok: true,
              json: () =>
                Promise.resolve({
                  file_id: 'test-id',
                  filename: 'test.pdf',
                  file_size: 1000,
                }),
            });
          }, 100);
        })
    );
    global.fetch = mockFetch;

    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);

    const fileInput = screen.getByRole('button');
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    const hiddenInput = fileInput.querySelector('input[type="file"]') as HTMLInputElement;
    if (hiddenInput) {
      fireEvent.change(hiddenInput, { target: { files: [file] } });
    }

    expect(screen.getByText('Uploading...')).toBeInTheDocument();

    await waitFor(() => {
      expect(mockOnUploadSuccess).toHaveBeenCalledWith({
        file_id: 'test-id',
        filename: 'test.pdf',
        file_size: 1000,
      });
    });
  });
});
