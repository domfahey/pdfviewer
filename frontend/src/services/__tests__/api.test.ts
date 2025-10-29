/**
 * Comprehensive unit tests for ApiService.
 * 
 * Tests cover file upload, metadata retrieval, file deletion,
 * error handling, and health check functionality.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiService } from '../api';
import type { PDFUploadResponse, PDFMetadata } from '../../types/pdf.types';

// Mock global fetch
global.fetch = vi.fn();

describe('ApiService', () => {
  const mockUploadResponse: PDFUploadResponse = {
    file_id: 'test-file-123',
    filename: 'test.pdf',
    file_size: 1024000,
    mime_type: 'application/pdf',
    upload_time: '2025-01-01T00:00:00Z',
    metadata: {
      page_count: 10,
      file_size: 1024000,
      encrypted: false,
      title: 'Test Document',
    },
  };

  const mockMetadata: PDFMetadata = {
    page_count: 10,
    file_size: 1024000,
    encrypted: false,
    title: 'Test Document',
    author: 'Test Author',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('uploadPDF', () => {
    it('should successfully upload a PDF file', async () => {
      const mockFile = new File(['test content'], 'test.pdf', {
        type: 'application/pdf',
      });

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => mockUploadResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      } as Response);

      const result = await ApiService.uploadPDF(mockFile);

      expect(result).toEqual(mockUploadResponse);
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/upload',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData),
        })
      );
    });

    it('should send file in FormData', async () => {
      const mockFile = new File(['test'], 'test.pdf', {
        type: 'application/pdf',
      });

      let capturedFormData: FormData | null = null;

      vi.mocked(fetch).mockImplementation(async (url, options) => {
        capturedFormData = options?.body as FormData;
        return {
          ok: true,
          status: 200,
          json: async () => mockUploadResponse,
          headers: new Headers(),
        } as Response;
      });

      await ApiService.uploadPDF(mockFile);

      expect(capturedFormData).toBeInstanceOf(FormData);
      expect(capturedFormData?.get('file')).toBe(mockFile);
    });

    it('should handle upload failure with error response', async () => {
      const errorResponse = { detail: 'File too large' };

      vi.mocked(fetch).mockResolvedValue({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        text: async () => JSON.stringify(errorResponse),
        headers: new Headers(),
      } as Response);

      const mockFile = new File(['test'], 'test.pdf', {
        type: 'application/pdf',
      });

      await expect(ApiService.uploadPDF(mockFile)).rejects.toThrow(
        'File too large'
      );
    });

    it('should handle upload failure with non-JSON error', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: async () => 'Server error occurred',
        headers: new Headers(),
      } as Response);

      const mockFile = new File(['test'], 'test.pdf', {
        type: 'application/pdf',
      });

      await expect(ApiService.uploadPDF(mockFile)).rejects.toThrow(
        'Upload failed with status 500'
      );
    });

    it('should handle network error', async () => {
      vi.mocked(fetch).mockRejectedValue(new Error('Network error'));

      const mockFile = new File(['test'], 'test.pdf', {
        type: 'application/pdf',
      });

      await expect(ApiService.uploadPDF(mockFile)).rejects.toThrow(
        'Network error'
      );
    });

    it('should handle JSON parse error in error response', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        text: async () => 'Invalid JSON {',
        headers: new Headers(),
      } as Response);

      const mockFile = new File(['test'], 'test.pdf', {
        type: 'application/pdf',
      });

      await expect(ApiService.uploadPDF(mockFile)).rejects.toThrow(
        'Upload failed with status 400'
      );
    });
  });

  describe('getPDFMetadata', () => {
    it('should successfully fetch PDF metadata', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockMetadata,
        headers: new Headers(),
      } as Response);

      const result = await ApiService.getPDFMetadata('test-file-123');

      expect(result).toEqual(mockMetadata);
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/metadata/test-file-123'
      );
    });

    it('should handle metadata fetch failure', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: new Headers(),
      } as Response);

      await expect(
        ApiService.getPDFMetadata('nonexistent-id')
      ).rejects.toThrow('Failed to fetch metadata');
    });

    it('should fetch metadata for different file IDs', async () => {
      const metadata1 = { ...mockMetadata, title: 'Document 1' };
      const metadata2 = { ...mockMetadata, title: 'Document 2' };

      vi.mocked(fetch)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => metadata1,
          headers: new Headers(),
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => metadata2,
          headers: new Headers(),
        } as Response);

      const result1 = await ApiService.getPDFMetadata('file-1');
      const result2 = await ApiService.getPDFMetadata('file-2');

      expect(result1.title).toBe('Document 1');
      expect(result2.title).toBe('Document 2');
      expect(fetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('getPDFUrl', () => {
    it('should return correct PDF URL', () => {
      const url = ApiService.getPDFUrl('test-file-123');

      expect(url).toBe('http://localhost:8000/api/pdf/test-file-123');
    });

    it('should return different URLs for different file IDs', () => {
      const url1 = ApiService.getPDFUrl('file-1');
      const url2 = ApiService.getPDFUrl('file-2');

      expect(url1).toBe('http://localhost:8000/api/pdf/file-1');
      expect(url2).toBe('http://localhost:8000/api/pdf/file-2');
    });

    it('should handle special characters in file ID', () => {
      const url = ApiService.getPDFUrl('file-with-dashes-123');

      expect(url).toContain('file-with-dashes-123');
    });
  });

  describe('deletePDF', () => {
    it('should successfully delete a PDF', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        status: 204,
        statusText: 'No Content',
        headers: new Headers(),
      } as Response);

      await expect(
        ApiService.deletePDF('test-file-123')
      ).resolves.toBeUndefined();

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/pdf/test-file-123',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });

    it('should handle delete failure', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: new Headers(),
      } as Response);

      await expect(ApiService.deletePDF('nonexistent-id')).rejects.toThrow(
        'Failed to delete file'
      );
    });

    it('should handle network error on delete', async () => {
      vi.mocked(fetch).mockRejectedValue(new Error('Network error'));

      await expect(ApiService.deletePDF('test-file-123')).rejects.toThrow(
        'Network error'
      );
    });

    it('should delete different files', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        status: 204,
        headers: new Headers(),
      } as Response);

      await ApiService.deletePDF('file-1');
      await ApiService.deletePDF('file-2');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/pdf/file-1',
        expect.any(Object)
      );
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/pdf/file-2',
        expect.any(Object)
      );
    });
  });

  describe('healthCheck', () => {
    it('should successfully perform health check', async () => {
      const healthResponse = {
        status: 'healthy',
        version: '0.1.0',
        timestamp: '2025-01-01T00:00:00Z',
      };

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => healthResponse,
        headers: new Headers(),
      } as Response);

      const result = await ApiService.healthCheck();

      expect(result).toEqual(healthResponse);
      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/health');
    });

    it('should return health check data even if unhealthy', async () => {
      const unhealthyResponse = {
        status: 'unhealthy',
        version: '0.1.0',
        error: 'Database connection failed',
      };

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => unhealthyResponse,
        headers: new Headers(),
      } as Response);

      const result = await ApiService.healthCheck();

      expect(result).toEqual(unhealthyResponse);
    });

    it('should handle health check network error', async () => {
      vi.mocked(fetch).mockRejectedValue(new Error('Connection refused'));

      await expect(ApiService.healthCheck()).rejects.toThrow(
        'Connection refused'
      );
    });
  });

  describe('API Base URL', () => {
    it('should use correct base URL for all endpoints', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({}),
        headers: new Headers(),
      } as Response);

      const baseUrl = 'http://localhost:8000/api';

      // Upload
      const mockFile = new File(['test'], 'test.pdf', {
        type: 'application/pdf',
      });
      await ApiService.uploadPDF(mockFile).catch(() => {});

      expect(fetch).toHaveBeenCalledWith(
        `${baseUrl}/upload`,
        expect.any(Object)
      );

      // Metadata
      await ApiService.getPDFMetadata('test-id').catch(() => {});
      expect(fetch).toHaveBeenCalledWith(`${baseUrl}/metadata/test-id`);

      // Delete
      await ApiService.deletePDF('test-id').catch(() => {});
      expect(fetch).toHaveBeenCalledWith(
        `${baseUrl}/pdf/test-id`,
        expect.any(Object)
      );

      // Health
      await ApiService.healthCheck().catch(() => {});
      expect(fetch).toHaveBeenCalledWith(`${baseUrl}/health`);

      // Get URL
      const pdfUrl = ApiService.getPDFUrl('test-id');
      expect(pdfUrl).toBe(`${baseUrl}/pdf/test-id`);
    });
  });

  describe('Error Handling', () => {
    it('should handle timeout errors', async () => {
      vi.mocked(fetch).mockRejectedValue(new Error('Request timeout'));

      const mockFile = new File(['test'], 'test.pdf', {
        type: 'application/pdf',
      });

      await expect(ApiService.uploadPDF(mockFile)).rejects.toThrow(
        'Request timeout'
      );
    });

    it('should handle CORS errors', async () => {
      vi.mocked(fetch).mockRejectedValue(
        new Error('CORS policy blocked request')
      );

      const mockFile = new File(['test'], 'test.pdf', {
        type: 'application/pdf',
      });

      await expect(ApiService.uploadPDF(mockFile)).rejects.toThrow('CORS');
    });

    it('should handle empty response body', async () => {
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => null,
        headers: new Headers(),
      } as Response);

      const result = await ApiService.healthCheck();

      expect(result).toBeNull();
    });
  });

  describe('Response Headers', () => {
    it('should handle responses with various headers', async () => {
      const headers = new Headers({
        'content-type': 'application/json',
        'x-request-id': 'test-123',
        'x-correlation-id': 'corr-456',
      });

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockUploadResponse,
        headers,
      } as Response);

      const mockFile = new File(['test'], 'test.pdf', {
        type: 'application/pdf',
      });

      const result = await ApiService.uploadPDF(mockFile);

      expect(result).toEqual(mockUploadResponse);
    });
  });
});
