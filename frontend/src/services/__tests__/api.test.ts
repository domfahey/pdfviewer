import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiService } from '../api';
import type { PDFUploadResponse, PDFMetadata } from '../../types/pdf.types';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('ApiService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('uploadPDF', () => {
    it('should successfully upload a PDF file', async () => {
      const mockResponse: PDFUploadResponse = {
        file_id: 'test-file-id',
        filename: 'test.pdf',
        file_size: 1024000,
        mime_type: 'application/pdf',
        upload_time: '2023-01-01T00:00:00Z',
        metadata: {
          page_count: 10,
          file_size: 1024000,
          encrypted: false,
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: {
          entries: () => [['content-type', 'application/json']],
        },
        json: () => Promise.resolve(mockResponse),
      });

      const testFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      const result = await ApiService.uploadPDF(testFile);

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/upload', {
        method: 'POST',
        body: expect.any(FormData),
      });

      // Verify FormData was created correctly
      const [, options] = mockFetch.mock.calls[0];
      const formData = options.body as FormData;
      expect(formData.get('file')).toBe(testFile);

      expect(result).toEqual(mockResponse);
    });

    it('should handle HTTP error responses with JSON error details', async () => {
      const errorResponse = {
        detail: 'File too large',
        code: 'FILE_SIZE_EXCEEDED',
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 413,
        statusText: 'Payload Too Large',
        headers: {
          entries: () => [],
        },
        text: () => Promise.resolve(JSON.stringify(errorResponse)),
      });

      const testFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      await expect(ApiService.uploadPDF(testFile)).rejects.toThrow('File too large');
    });

    it('should handle HTTP error responses with plain text', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: {
          entries: () => [],
        },
        text: () => Promise.resolve('Internal server error occurred'),
      });

      const testFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      await expect(ApiService.uploadPDF(testFile)).rejects.toThrow(
        'Upload failed with status 500: Internal server error occurred'
      );
    });

    it('should handle HTTP error responses with invalid JSON', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        headers: {
          entries: () => [],
        },
        text: () => Promise.resolve('Invalid JSON {'),
      });

      const testFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      await expect(ApiService.uploadPDF(testFile)).rejects.toThrow(
        'Upload failed with status 400: Invalid JSON {'
      );
    });

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const testFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      await expect(ApiService.uploadPDF(testFile)).rejects.toThrow('Network error');
    });

    it('should handle fetch timeout', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Request timeout'));

      const testFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      await expect(ApiService.uploadPDF(testFile)).rejects.toThrow('Request timeout');
    });

    it('should handle response parsing errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: {
          entries: () => [],
        },
        json: () => Promise.reject(new Error('Invalid JSON response')),
      });

      const testFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      await expect(ApiService.uploadPDF(testFile)).rejects.toThrow('Invalid JSON response');
    });
  });

  describe('getPDFMetadata', () => {
    it('should successfully fetch PDF metadata', async () => {
      const mockMetadata: PDFMetadata = {
        title: 'Test Document',
        author: 'Test Author',
        subject: 'Test Subject',
        creator: 'Test Creator',
        producer: 'Test Producer',
        creation_date: '2023-01-01T00:00:00Z',
        modification_date: '2023-01-02T00:00:00Z',
        page_count: 10,
        file_size: 1024000,
        encrypted: false,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockMetadata),
      });

      const result = await ApiService.getPDFMetadata('test-file-id');

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/metadata/test-file-id');
      expect(result).toEqual(mockMetadata);
    });

    it('should handle 404 error for non-existent file', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      });

      await expect(ApiService.getPDFMetadata('non-existent-id')).rejects.toThrow(
        'Failed to fetch metadata'
      );
    });

    it('should handle server errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      await expect(ApiService.getPDFMetadata('test-file-id')).rejects.toThrow(
        'Failed to fetch metadata'
      );
    });

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(ApiService.getPDFMetadata('test-file-id')).rejects.toThrow('Network error');
    });
  });

  describe('getPDFUrl', () => {
    it('should return correct PDF URL', () => {
      const fileId = 'test-file-id';
      const expectedUrl = 'http://localhost:8000/api/pdf/test-file-id';

      const result = ApiService.getPDFUrl(fileId);

      expect(result).toBe(expectedUrl);
    });

    it('should handle special characters in file ID', () => {
      const fileId = 'test-file-id-with-special-chars_123';
      const expectedUrl = 'http://localhost:8000/api/pdf/test-file-id-with-special-chars_123';

      const result = ApiService.getPDFUrl(fileId);

      expect(result).toBe(expectedUrl);
    });

    it('should handle empty file ID', () => {
      const fileId = '';
      const expectedUrl = 'http://localhost:8000/api/pdf/';

      const result = ApiService.getPDFUrl(fileId);

      expect(result).toBe(expectedUrl);
    });
  });

  describe('deletePDF', () => {
    it('should successfully delete a PDF file', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        statusText: 'No Content',
      });

      await expect(ApiService.deletePDF('test-file-id')).resolves.toBeUndefined();

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/pdf/test-file-id', {
        method: 'DELETE',
      });
    });

    it('should handle 404 error for non-existent file', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      });

      await expect(ApiService.deletePDF('non-existent-id')).rejects.toThrow(
        'Failed to delete file'
      );
    });

    it('should handle server errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      await expect(ApiService.deletePDF('test-file-id')).rejects.toThrow('Failed to delete file');
    });

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(ApiService.deletePDF('test-file-id')).rejects.toThrow('Network error');
    });

    it('should handle forbidden access', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        statusText: 'Forbidden',
      });

      await expect(ApiService.deletePDF('restricted-file-id')).rejects.toThrow(
        'Failed to delete file'
      );
    });
  });

  describe('healthCheck', () => {
    it('should successfully perform health check', async () => {
      const mockHealthResponse = {
        status: 'healthy',
        timestamp: '2023-01-01T00:00:00Z',
        version: '1.0.0',
        uptime: 3600,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockHealthResponse),
      });

      const result = await ApiService.healthCheck();

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/health');
      expect(result).toEqual(mockHealthResponse);
    });

    it('should handle unhealthy service response', async () => {
      const mockUnhealthyResponse = {
        status: 'unhealthy',
        error: 'Database connection failed',
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 503,
        json: () => Promise.resolve(mockUnhealthyResponse),
      });

      const result = await ApiService.healthCheck();

      expect(result).toEqual(mockUnhealthyResponse);
    });

    it('should handle network errors during health check', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Connection refused'));

      await expect(ApiService.healthCheck()).rejects.toThrow('Connection refused');
    });

    it('should handle invalid JSON response in health check', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.reject(new Error('Invalid JSON')),
      });

      await expect(ApiService.healthCheck()).rejects.toThrow('Invalid JSON');
    });
  });

  describe('error handling edge cases', () => {
    it('should handle fetch throwing non-Error objects', async () => {
      mockFetch.mockRejectedValueOnce('String error');

      const testFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      await expect(ApiService.uploadPDF(testFile)).rejects.toThrow('String error');
    });

    it('should handle response with missing required methods', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        // Missing json method
      } as Partial<Response>);

      const testFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      await expect(ApiService.uploadPDF(testFile)).rejects.toThrow();
    });

    it('should handle partial response data', async () => {
      const partialResponse = {
        file_id: 'test-id',
        filename: 'test.pdf',
        // Missing other required fields
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: {
          entries: () => [],
        },
        json: () => Promise.resolve(partialResponse),
      });

      const testFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

      const result = await ApiService.uploadPDF(testFile);

      // Should still return the partial response
      expect(result).toEqual(partialResponse);
    });
  });

  describe('request formatting', () => {
    it('should set correct headers for FormData uploads', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: {
          entries: () => [],
        },
        json: () => Promise.resolve({ file_id: 'test' }),
      });

      const testFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      await ApiService.uploadPDF(testFile);

      const [url, options] = mockFetch.mock.calls[0];

      expect(url).toBe('http://localhost:8000/api/upload');
      expect(options.method).toBe('POST');
      expect(options.body).toBeInstanceOf(FormData);
      // Note: Don't explicitly set Content-Type for FormData, browser handles it
      expect(options.headers).toBeUndefined();
    });

    it('should handle files with different MIME types', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: {
          entries: () => [],
        },
        json: () => Promise.resolve({ file_id: 'test' }),
      });

      const testFile = new File(['content'], 'document.pdf', {
        type: 'application/pdf',
      });

      await ApiService.uploadPDF(testFile);

      const formData = mockFetch.mock.calls[0][1].body as FormData;
      const uploadedFile = formData.get('file') as File;

      expect(uploadedFile.type).toBe('application/pdf');
      expect(uploadedFile.name).toBe('document.pdf');
    });
  });
});
