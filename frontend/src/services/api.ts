import type { PDFUploadResponse, PDFMetadata } from '../types/pdf.types';

const API_BASE_URL = 'http://localhost:8000/api';

export class ApiService {
  static async uploadPDF(file: File): Promise<PDFUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
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
