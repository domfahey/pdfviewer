import type { PDFUploadResponse, PDFMetadata } from '../types/pdf.types';
import { devLog, devError } from '../utils/devLogger';

const API_BASE_URL = 'http://localhost:8000/api';

export class ApiService {
  static async uploadPDF(file: File): Promise<PDFUploadResponse> {
    devLog('🌐 [ApiService] Preparing upload request:', {
      url: `${API_BASE_URL}/upload`,
      fileName: file.name,
      fileSize: file.size,
    });

    const formData = new FormData();
    formData.append('file', file);

    try {
      devLog('📡 [ApiService] Sending POST request to backend...');
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      devLog('📥 [ApiService] Response received:', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
      });

      if (!response.ok) {
        const errorText = await response.text();
        devError('❌ [ApiService] Upload failed with error response:', {
          status: response.status,
          statusText: response.statusText,
          errorBody: errorText,
        });

        try {
          const error = JSON.parse(errorText);
          throw new Error(error.detail || 'Upload failed');
        } catch {
          throw new Error(`Upload failed with status ${response.status}: ${errorText}`);
        }
      }

      const responseData = await response.json();
      devLog('✅ [ApiService] Upload completed successfully:', responseData);
      return responseData;
    } catch (error) {
      devError('🚨 [ApiService] Network or parsing error:', {
        error,
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined,
      });
      throw error;
    }
  }

  static async getPDFMetadata(fileId: string): Promise<PDFMetadata> {
    const response = await fetch(`${API_BASE_URL}/metadata/${fileId}`);

    if (!response.ok) {
      throw new Error('Failed to fetch metadata');
    }

    return response.json();
  }

  static getPDFUrl(fileId: string): string {
    return `${API_BASE_URL}/pdf/${fileId}`;
  }

  static async deletePDF(fileId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/pdf/${fileId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete file');
    }
  }

  static async healthCheck(): Promise<unknown> {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  }
}
