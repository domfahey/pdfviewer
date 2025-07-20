import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FileUpload } from '../Upload/FileUpload';

// Mock the useFileUpload hook
vi.mock('../../hooks/useFileUpload', () => ({
  useFileUpload: vi.fn(),
}));

// Import the mocked hook for type safety
import { useFileUpload } from '../../hooks/useFileUpload';
const mockUseFileUpload = vi.mocked(useFileUpload);

describe('FileUpload', () => {
  const mockOnUploadSuccess = vi.fn();
  const mockUploadFile = vi.fn();
  const mockClearError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    mockUseFileUpload.mockReturnValue({
      uploading: false,
      uploadProgress: 0,
      error: null,
      uploadFile: mockUploadFile,
      clearError: mockClearError,
    });
  });

  it('renders upload interface', () => {
    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);

    expect(screen.getByText('Drop your PDF here')).toBeInTheDocument();
    expect(screen.getByText('or click to browse files')).toBeInTheDocument();
    expect(screen.getByText('Maximum file size: 50MB')).toBeInTheDocument();
  });

  it('shows uploading state when uploading', () => {
    mockUseFileUpload.mockReturnValue({
      uploading: true,
      uploadProgress: 50,
      error: null,
      uploadFile: mockUploadFile,
      clearError: mockClearError,
    });

    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);

    expect(screen.getByText('Uploading...')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('shows error state when there is an error', () => {
    mockUseFileUpload.mockReturnValue({
      uploading: false,
      uploadProgress: 0,
      error: 'Upload failed',
      uploadFile: mockUploadFile,
      clearError: mockClearError,
    });

    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);

    expect(screen.getByText('Upload Error')).toBeInTheDocument();
    expect(screen.getByText('Upload failed')).toBeInTheDocument();
  });

  it('calls uploadFile when a file is selected', async () => {
    mockUploadFile.mockResolvedValue({
      file_id: 'test-id',
      filename: 'test.pdf',
      file_size: 1000,
    });

    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [file] } });
    });

    expect(mockUploadFile).toHaveBeenCalledWith(file);
  });

  it('calls onUploadSuccess when upload completes', async () => {
    const uploadResult = {
      file_id: 'test-id',
      filename: 'test.pdf',
      file_size: 1000,
    };

    mockUploadFile.mockResolvedValue(uploadResult);

    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [file] } });
    });

    await waitFor(() => {
      expect(mockOnUploadSuccess).toHaveBeenCalledWith(uploadResult);
    });
  });

  it('handles drag and drop', async () => {
    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);

    const dropZone = screen.getByText('Drop your PDF here').closest('div');
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    await act(async () => {
      fireEvent.drop(dropZone!, {
        dataTransfer: {
          files: [file],
        },
      });
    });

    expect(mockUploadFile).toHaveBeenCalledWith(file);
  });

  it('clears error when clearError is called', async () => {
    mockUseFileUpload.mockReturnValue({
      uploading: false,
      uploadProgress: 0,
      error: 'Upload failed',
      uploadFile: mockUploadFile,
      clearError: mockClearError,
    });

    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);

    const clearButton = screen.getByRole('button');
    
    await act(async () => {
      fireEvent.click(clearButton);
    });

    expect(mockClearError).toHaveBeenCalled();
  });
});