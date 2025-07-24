import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useFileUpload } from '../useFileUpload';
import { ApiService } from '../../services/api';
import type { PDFUploadResponse } from '../../types/pdf.types';

// Mock the ApiService
vi.mock('../../services/api', () => ({
  ApiService: {
    uploadPDF: vi.fn(),
  },
}));

const mockApiService = vi.mocked(ApiService);

describe('useFileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useFileUpload());

    expect(result.current.uploading).toBe(false);
    expect(result.current.uploadProgress).toBe(0);
    expect(result.current.error).toBe(null);
    expect(typeof result.current.uploadFile).toBe('function');
    expect(typeof result.current.clearError).toBe('function');
  });

  describe('validateFile', () => {
    it('should reject non-PDF files based on MIME type', async () => {
      const { result } = renderHook(() => useFileUpload());

      const textFile = new File(['test'], 'test.txt', { type: 'text/plain' });

      await act(async () => {
        const response = await result.current.uploadFile(textFile);
        expect(response).toBe(null);
      });

      expect(result.current.error).toBe('Only PDF files are allowed');
      expect(result.current.uploading).toBe(false);
    });

    it('should reject non-PDF files based on filename', async () => {
      const { result } = renderHook(() => useFileUpload());

      const textFile = new File(['test'], 'test.txt', { type: '' });

      await act(async () => {
        const response = await result.current.uploadFile(textFile);
        expect(response).toBe(null);
      });

      expect(result.current.error).toBe('Only PDF files are allowed');
      expect(result.current.uploading).toBe(false);
    });

    it('should accept PDF files with correct MIME type', async () => {
      const { result } = renderHook(() => useFileUpload());

      const mockResponse: PDFUploadResponse = {
        file_id: 'test-id',
        filename: 'test.pdf',
        file_size: 1000,
        mime_type: 'application/pdf',
        upload_time: '2023-01-01T00:00:00Z',
      };

      mockApiService.uploadPDF.mockResolvedValue(mockResponse);

      const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      let uploadResult: PDFUploadResponse | null = null;

      // Start upload
      const uploadPromise = act(async () => {
        uploadResult = await result.current.uploadFile(pdfFile);
      });

      // Fast-forward timers to complete progress simulation
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      // Wait for upload to complete
      await uploadPromise;

      // Fast-forward cleanup timer
      act(() => {
        vi.advanceTimersByTime(500);
      });

      expect(uploadResult).toEqual(mockResponse);
      expect(result.current.error).toBe(null);
      expect(result.current.uploading).toBe(false);
    });

    it('should accept PDF files with .pdf extension', async () => {
      const { result } = renderHook(() => useFileUpload());

      const mockResponse: PDFUploadResponse = {
        file_id: 'test-id',
        filename: 'test.pdf',
        file_size: 1000,
        mime_type: 'application/pdf',
        upload_time: '2023-01-01T00:00:00Z',
      };

      mockApiService.uploadPDF.mockResolvedValue(mockResponse);

      // File without MIME type but with .pdf extension
      const pdfFile = new File(['pdf content'], 'test.PDF', { type: '' });

      let uploadResult: PDFUploadResponse | null = null;

      // Start upload
      const uploadPromise = act(async () => {
        uploadResult = await result.current.uploadFile(pdfFile);
      });

      // Fast-forward timers
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      // Wait for upload to complete
      await uploadPromise;

      // Fast-forward cleanup timer
      act(() => {
        vi.advanceTimersByTime(500);
      });

      expect(uploadResult).toEqual(mockResponse);
      expect(result.current.error).toBe(null);
      expect(result.current.uploading).toBe(false);
    });

    it('should reject files larger than 50MB', async () => {
      const { result } = renderHook(() => useFileUpload());

      // Create a large file (51MB)
      const largeFile = new File(['x'.repeat(51 * 1024 * 1024)], 'large.pdf', {
        type: 'application/pdf',
      });

      await act(async () => {
        const response = await result.current.uploadFile(largeFile);
        expect(response).toBe(null);
      });

      expect(result.current.error).toBe('File size must be less than 50MB');
      expect(result.current.uploading).toBe(false);
    });
  });

  describe('uploadFile', () => {
    it('should handle successful upload', async () => {
      const { result } = renderHook(() => useFileUpload());

      const mockResponse: PDFUploadResponse = {
        file_id: 'test-id',
        filename: 'test.pdf',
        file_size: 1000,
        mime_type: 'application/pdf',
        upload_time: '2023-01-01T00:00:00Z',
        metadata: {
          page_count: 10,
          file_size: 1000,
          encrypted: false,
        },
      };

      mockApiService.uploadPDF.mockResolvedValue(mockResponse);

      const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      let uploadResult: PDFUploadResponse | null = null;

      // Start upload
      const uploadPromise = act(async () => {
        uploadResult = await result.current.uploadFile(pdfFile);
      });

      // Fast-forward timers to complete progress and cleanup
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      // Wait for upload to complete
      await uploadPromise;

      // Fast-forward cleanup timer
      act(() => {
        vi.advanceTimersByTime(500);
      });

      expect(mockApiService.uploadPDF).toHaveBeenCalledWith(pdfFile);
      expect(uploadResult).toEqual(mockResponse);
      expect(result.current.uploading).toBe(false);
      expect(result.current.uploadProgress).toBe(0); // Reset after completion
    });

    it('should handle upload progress simulation', async () => {
      const { result } = renderHook(() => useFileUpload());

      const mockResponse: PDFUploadResponse = {
        file_id: 'test-id',
        filename: 'test.pdf',
        file_size: 1000,
        mime_type: 'application/pdf',
        upload_time: '2023-01-01T00:00:00Z',
      };

      // Make the API call resolve immediately
      mockApiService.uploadPDF.mockResolvedValue(mockResponse);

      const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      // Start upload without waiting
      let uploadPromise: Promise<void>;
      act(() => {
        uploadPromise = result.current.uploadFile(pdfFile).then(() => {});
      });

      // Check initial state after starting upload
      expect(result.current.uploading).toBe(true);
      expect(result.current.uploadProgress).toBe(0);

      // Advance progress simulation
      act(() => {
        vi.advanceTimersByTime(300); // Advance 3 intervals of 100ms
      });

      expect(result.current.uploadProgress).toBe(30);

      // Complete the upload and timers
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      await act(async () => {
        await uploadPromise!;
      });

      expect(result.current.uploading).toBe(false);
    });

    it('should handle API errors', async () => {
      const { result } = renderHook(() => useFileUpload());

      const errorMessage = 'Upload failed due to server error';
      mockApiService.uploadPDF.mockRejectedValue(new Error(errorMessage));

      const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      let uploadResult: PDFUploadResponse | null = null;
      await act(async () => {
        uploadResult = await result.current.uploadFile(pdfFile);
      });

      expect(uploadResult).toBe(null);
      expect(result.current.error).toBe(errorMessage);
      expect(result.current.uploading).toBe(false);
      expect(result.current.uploadProgress).toBe(0);
    });

    it('should handle non-Error exceptions', async () => {
      const { result } = renderHook(() => useFileUpload());

      mockApiService.uploadPDF.mockRejectedValue('String error');

      const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      let uploadResult: PDFUploadResponse | null = null;
      await act(async () => {
        uploadResult = await result.current.uploadFile(pdfFile);
      });

      expect(uploadResult).toBe(null);
      expect(result.current.error).toBe('Upload failed');
      expect(result.current.uploading).toBe(false);
      expect(result.current.uploadProgress).toBe(0);
    });
  });

  describe('clearError', () => {
    it('should clear error state', async () => {
      const { result } = renderHook(() => useFileUpload());

      // First, cause an error
      const textFile = new File(['test'], 'test.txt', { type: 'text/plain' });

      await act(async () => {
        await result.current.uploadFile(textFile);
      });

      expect(result.current.error).toBe('Only PDF files are allowed');

      // Then clear the error
      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBe(null);
    });
  });

  describe('state management', () => {
    it('should reset progress and uploading state after successful upload', async () => {
      const { result } = renderHook(() => useFileUpload());

      const mockResponse: PDFUploadResponse = {
        file_id: 'test-id',
        filename: 'test.pdf',
        file_size: 1000,
        mime_type: 'application/pdf',
        upload_time: '2023-01-01T00:00:00Z',
      };

      mockApiService.uploadPDF.mockResolvedValue(mockResponse);

      const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      // Start upload
      const uploadPromise = act(async () => {
        await result.current.uploadFile(pdfFile);
      });

      // Complete progress and cleanup timers
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      await uploadPromise;

      expect(result.current.uploading).toBe(false);
      expect(result.current.uploadProgress).toBe(0);
    });

    it('should clear previous error when starting new upload', async () => {
      const { result } = renderHook(() => useFileUpload());

      // First, cause an error
      const textFile = new File(['test'], 'test.txt', { type: 'text/plain' });
      await act(async () => {
        await result.current.uploadFile(textFile);
      });
      expect(result.current.error).toBe('Only PDF files are allowed');

      // Then start a valid upload
      const mockResponse: PDFUploadResponse = {
        file_id: 'test-id',
        filename: 'test.pdf',
        file_size: 1000,
        mime_type: 'application/pdf',
        upload_time: '2023-01-01T00:00:00Z',
      };

      mockApiService.uploadPDF.mockResolvedValue(mockResponse);
      const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      await act(async () => {
        await result.current.uploadFile(pdfFile);
      });

      expect(result.current.error).toBe(null);
    });
  });

  describe('edge cases', () => {
    it('should handle empty file name validation', async () => {
      const { result } = renderHook(() => useFileUpload());

      const fileWithEmptyName = new File(['content'], '', { type: 'application/pdf' });

      const mockResponse: PDFUploadResponse = {
        file_id: 'test-id',
        filename: 'test.pdf',
        file_size: 1000,
        mime_type: 'application/pdf',
        upload_time: '2023-01-01T00:00:00Z',
      };

      mockApiService.uploadPDF.mockResolvedValue(mockResponse);

      let uploadResult: PDFUploadResponse | null = null;

      // Start upload
      const uploadPromise = act(async () => {
        uploadResult = await result.current.uploadFile(fileWithEmptyName);
      });

      // Fast-forward timers
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      await uploadPromise;

      // Should accept based on MIME type even with empty filename
      expect(uploadResult).toEqual(mockResponse);
      expect(result.current.error).toBe(null);
      expect(result.current.uploading).toBe(false);
    });

    it('should handle file at exactly 50MB limit', async () => {
      const { result } = renderHook(() => useFileUpload());

      // Create a file at exactly 50MB
      const exactLimitFile = new File(['x'.repeat(50 * 1024 * 1024)], 'limit.pdf', {
        type: 'application/pdf',
      });

      const mockResponse: PDFUploadResponse = {
        file_id: 'test-id',
        filename: 'limit.pdf',
        file_size: 50 * 1024 * 1024,
        mime_type: 'application/pdf',
        upload_time: '2023-01-01T00:00:00Z',
      };

      mockApiService.uploadPDF.mockResolvedValue(mockResponse);

      let uploadResult: PDFUploadResponse | null = null;

      // Start upload
      const uploadPromise = act(async () => {
        uploadResult = await result.current.uploadFile(exactLimitFile);
      });

      // Fast-forward timers
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      await uploadPromise;

      expect(uploadResult).toEqual(mockResponse);
      expect(result.current.error).toBe(null);
      expect(result.current.uploading).toBe(false);
    });
  });
});
