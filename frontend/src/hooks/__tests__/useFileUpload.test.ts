/**
 * Comprehensive unit tests for useFileUpload hook.
 *
 * Tests cover file upload, validation, progress tracking,
 * error handling, and state management.
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useFileUpload } from '../useFileUpload';
import { ApiService } from '../../services/api';
import type { PDFUploadResponse } from '../../types/pdf.types';

// Mock ApiService
vi.mock('../../services/api', () => ({
  ApiService: {
    uploadPDF: vi.fn(),
  },
}));

describe('useFileUpload', () => {
  const mockUploadResponse: PDFUploadResponse = {
    file_id: 'test-file-123',
    filename: 'test.pdf',
    file_size: 1024000,
    metadata: {
      page_count: 10,
      file_size: 1024000,
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useFileUpload());

      expect(result.current.uploading).toBe(false);
      expect(result.current.uploadProgress).toBe(0);
      expect(result.current.error).toBeNull();
    });

    it('should provide all required functions', () => {
      const { result } = renderHook(() => useFileUpload());

      expect(typeof result.current.uploadFile).toBe('function');
      expect(typeof result.current.clearError).toBe('function');
    });
  });

  describe('File Validation', () => {
    it('should accept valid PDF file', async () => {
      vi.mocked(ApiService.uploadPDF).mockResolvedValue(mockUploadResponse);

      const { result } = renderHook(() => useFileUpload());

      const validFile = new File(['test content'], 'test.pdf', {
        type: 'application/pdf',
      });

      let uploadResult: PDFUploadResponse | null = null;

      await act(async () => {
        uploadResult = await result.current.uploadFile(validFile);
      });

      expect(uploadResult).toEqual(mockUploadResponse);
      expect(result.current.error).toBeNull();
    });

    it('should reject non-PDF file by type', async () => {
      const { result } = renderHook(() => useFileUpload());

      const invalidFile = new File(['test content'], 'test.txt', {
        type: 'text/plain',
      });

      let uploadResult: PDFUploadResponse | null = null;

      await act(async () => {
        uploadResult = await result.current.uploadFile(invalidFile);
      });

      expect(uploadResult).toBeNull();
      expect(result.current.error).toBe('Only PDF files are allowed');
    });

    it('should accept PDF file with .pdf extension even without proper MIME type', async () => {
      vi.mocked(ApiService.uploadPDF).mockResolvedValue(mockUploadResponse);

      const { result } = renderHook(() => useFileUpload());

      const pdfFile = new File(['test content'], 'document.pdf', {
        type: 'application/octet-stream',
      });

      let uploadResult: PDFUploadResponse | null = null;

      await act(async () => {
        uploadResult = await result.current.uploadFile(pdfFile);
      });

      expect(uploadResult).toEqual(mockUploadResponse);
      expect(result.current.error).toBeNull();
    });

    it('should reject file larger than 50MB', async () => {
      const { result } = renderHook(() => useFileUpload());

      // Create a mock file object with size > 50MB
      const largeFile = new File(['x'.repeat(51 * 1024 * 1024)], 'large.pdf', {
        type: 'application/pdf',
      });

      // Mock the size property
      Object.defineProperty(largeFile, 'size', {
        value: 51 * 1024 * 1024,
      });

      let uploadResult: PDFUploadResponse | null = null;

      await act(async () => {
        uploadResult = await result.current.uploadFile(largeFile);
      });

      expect(uploadResult).toBeNull();
      expect(result.current.error).toContain('File size must be less than');
    });

    it('should accept file at exactly 50MB limit', async () => {
      vi.mocked(ApiService.uploadPDF).mockResolvedValue(mockUploadResponse);

      const { result } = renderHook(() => useFileUpload());

      const maxSizeFile = new File(['content'], 'max.pdf', {
        type: 'application/pdf',
      });

      Object.defineProperty(maxSizeFile, 'size', {
        value: 50 * 1024 * 1024,
      });

      let uploadResult: PDFUploadResponse | null = null;

      await act(async () => {
        uploadResult = await result.current.uploadFile(maxSizeFile);
      });

      expect(uploadResult).toEqual(mockUploadResponse);
      expect(result.current.error).toBeNull();
    });
  });

  describe('Upload Process', () => {
    it('should successfully upload a file', async () => {
      vi.mocked(ApiService.uploadPDF).mockResolvedValue(mockUploadResponse);

      const { result } = renderHook(() => useFileUpload());

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      let uploadResult: PDFUploadResponse | null = null;

      await act(async () => {
        uploadResult = await result.current.uploadFile(file);
      });

      expect(ApiService.uploadPDF).toHaveBeenCalledWith(file);
      expect(uploadResult).toEqual(mockUploadResponse);
    });

    it('should set uploading state during upload', async () => {
      vi.mocked(ApiService.uploadPDF).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockUploadResponse), 1000))
      );

      const { result } = renderHook(() => useFileUpload());

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      act(() => {
        result.current.uploadFile(file);
      });

      await waitFor(() => {
        expect(result.current.uploading).toBe(true);
      });

      await vi.advanceTimersByTimeAsync(1000);

      await waitFor(() => {
        expect(result.current.uploading).toBe(false);
      });
    });

    it('should track upload progress', async () => {
      vi.mocked(ApiService.uploadPDF).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockUploadResponse), 500))
      );

      const { result } = renderHook(() => useFileUpload());

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      act(() => {
        result.current.uploadFile(file);
      });

      // Progress should increase over time
      await act(async () => {
        await vi.advanceTimersByTimeAsync(100);
      });

      expect(result.current.uploadProgress).toBeGreaterThan(0);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(500);
      });

      // Progress should reach 100% after upload completes
      await waitFor(() => {
        expect(result.current.uploadProgress).toBe(100);
      });

      // Progress should reset after a delay
      await act(async () => {
        await vi.advanceTimersByTimeAsync(500);
      });

      expect(result.current.uploadProgress).toBe(0);
    });

    it('should handle upload failure', async () => {
      const errorMessage = 'Network error';
      vi.mocked(ApiService.uploadPDF).mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useFileUpload());

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      let uploadResult: PDFUploadResponse | null = null;

      await act(async () => {
        uploadResult = await result.current.uploadFile(file);
      });

      expect(uploadResult).toBeNull();
      expect(result.current.error).toBe(errorMessage);
      expect(result.current.uploading).toBe(false);
      expect(result.current.uploadProgress).toBe(0);
    });

    it('should reset progress on upload failure', async () => {
      vi.mocked(ApiService.uploadPDF).mockRejectedValue(new Error('Upload failed'));

      const { result } = renderHook(() => useFileUpload());

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      await act(async () => {
        await result.current.uploadFile(file);
      });

      expect(result.current.uploadProgress).toBe(0);
      expect(result.current.uploading).toBe(false);
    });
  });

  describe('Error Management', () => {
    it('should clear error when clearError is called', async () => {
      const { result } = renderHook(() => useFileUpload());

      const invalidFile = new File(['test'], 'test.txt', {
        type: 'text/plain',
      });

      await act(async () => {
        await result.current.uploadFile(invalidFile);
      });

      expect(result.current.error).toBeTruthy();

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });

    it('should clear previous error on new upload attempt', async () => {
      vi.mocked(ApiService.uploadPDF)
        .mockRejectedValueOnce(new Error('First error'))
        .mockResolvedValueOnce(mockUploadResponse);

      const { result } = renderHook(() => useFileUpload());

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      // First upload fails
      await act(async () => {
        await result.current.uploadFile(file);
      });

      expect(result.current.error).toBe('First error');

      // Second upload succeeds
      await act(async () => {
        await result.current.uploadFile(file);
      });

      expect(result.current.error).toBeNull();
    });

    it('should handle non-Error exceptions', async () => {
      vi.mocked(ApiService.uploadPDF).mockRejectedValue('String error');

      const { result } = renderHook(() => useFileUpload());

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      await act(async () => {
        await result.current.uploadFile(file);
      });

      expect(result.current.error).toBe('Upload failed');
    });
  });

  describe('Edge Cases', () => {
    it('should handle consecutive upload attempts', async () => {
      vi.mocked(ApiService.uploadPDF).mockResolvedValue(mockUploadResponse);

      const { result } = renderHook(() => useFileUpload());

      const file1 = new File(['test1'], 'test1.pdf', {
        type: 'application/pdf',
      });
      const file2 = new File(['test2'], 'test2.pdf', {
        type: 'application/pdf',
      });

      let result1: PDFUploadResponse | null = null;
      let result2: PDFUploadResponse | null = null;

      await act(async () => {
        result1 = await result.current.uploadFile(file1);
      });

      expect(result1).toEqual(mockUploadResponse);

      await act(async () => {
        result2 = await result.current.uploadFile(file2);
      });

      expect(result2).toEqual(mockUploadResponse);
      expect(ApiService.uploadPDF).toHaveBeenCalledTimes(2);
    });

    it('should handle validation error without calling API', async () => {
      const { result } = renderHook(() => useFileUpload());

      const invalidFile = new File(['test'], 'test.txt', {
        type: 'text/plain',
      });

      await act(async () => {
        await result.current.uploadFile(invalidFile);
      });

      expect(ApiService.uploadPDF).not.toHaveBeenCalled();
    });

    it('should clear validation error on new upload', async () => {
      vi.mocked(ApiService.uploadPDF).mockResolvedValue(mockUploadResponse);

      const { result } = renderHook(() => useFileUpload());

      const invalidFile = new File(['test'], 'test.txt', {
        type: 'text/plain',
      });

      // First upload fails validation
      await act(async () => {
        await result.current.uploadFile(invalidFile);
      });

      expect(result.current.error).toBe('Only PDF files are allowed');

      // Second upload with valid file
      const validFile = new File(['test'], 'test.pdf', {
        type: 'application/pdf',
      });

      await act(async () => {
        await result.current.uploadFile(validFile);
      });

      expect(result.current.error).toBeNull();
    });
  });
});
