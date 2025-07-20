import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import FileUpload from '../FileUpload';

// Mock the upload API
const mockOnUpload = vi.fn();

describe('FileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('renders upload interface', () => {
    render(<FileUpload onUpload={mockOnUpload} />);
    
    expect(screen.getByText('Choose PDF file')).toBeInTheDocument();
    expect(screen.getByText('or drag and drop')).toBeInTheDocument();
    expect(screen.getByText('PDF files only, max 50MB')).toBeInTheDocument();
  });

  it('handles file selection', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        file_id: 'test-id',
        filename: 'test.pdf',
        file_size: 1000,
      }),
    });
    global.fetch = mockFetch;

    render(<FileUpload onUpload={mockOnUpload} />);
    
    const fileInput = screen.getByLabelText(/choose pdf file/i);
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/upload', expect.any(Object));
    });
  });

  it('shows error for non-PDF files', () => {
    render(<FileUpload onUpload={mockOnUpload} />);
    
    const fileInput = screen.getByLabelText(/choose pdf file/i);
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    expect(screen.getByText('Please select a PDF file')).toBeInTheDocument();
  });

  it('shows error for files too large', () => {
    render(<FileUpload onUpload={mockOnUpload} />);
    
    const fileInput = screen.getByLabelText(/choose pdf file/i);
    const largeFile = new File(['x'.repeat(51 * 1024 * 1024)], 'large.pdf', { 
      type: 'application/pdf' 
    });
    
    Object.defineProperty(largeFile, 'size', { value: 51 * 1024 * 1024 });
    
    fireEvent.change(fileInput, { target: { files: [largeFile] } });
    
    expect(screen.getByText('File size must be less than 50MB')).toBeInTheDocument();
  });

  it('handles upload progress', async () => {
    const mockFetch = vi.fn().mockImplementation(() => 
      new Promise(resolve => {
        setTimeout(() => {
          resolve({
            ok: true,
            json: () => Promise.resolve({
              file_id: 'test-id',
              filename: 'test.pdf',
              file_size: 1000,
            }),
          });
        }, 100);
      })
    );
    global.fetch = mockFetch;

    render(<FileUpload onUpload={mockOnUpload} />);
    
    const fileInput = screen.getByLabelText(/choose pdf file/i);
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    expect(screen.getByText('Uploading...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(mockOnUpload).toHaveBeenCalledWith({
        file_id: 'test-id',
        filename: 'test.pdf',
        file_size: 1000,
      });
    });
  });
});