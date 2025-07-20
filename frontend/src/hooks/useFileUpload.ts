import { useState, useCallback } from 'react';
import { ApiService } from '../services/api';
import type { PDFUploadResponse } from '../types/pdf.types';

interface UseFileUploadReturn {
  uploading: boolean;
  uploadProgress: number;
  error: string | null;
  uploadFile: (file: File) => Promise<PDFUploadResponse | null>;
  clearError: () => void;
}

export const useFileUpload = (): UseFileUploadReturn => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const validateFile = (file: File): string | null => {
    // Check file type
    if (!file.type.includes('pdf') && !file.name.toLowerCase().endsWith('.pdf')) {
      return 'Only PDF files are allowed';
    }

    // Check file size (50MB limit)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      return `File size must be less than ${maxSize / (1024 * 1024)}MB`;
    }

    return null;
  };

  const uploadFile = useCallback(async (file: File): Promise<PDFUploadResponse | null> => {
    console.log('🚀 [FileUpload] Starting upload process:', {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      timestamp: new Date().toISOString(),
    });

    setError(null);
    setUploadProgress(0);

    // Validate file
    const validationError = validateFile(file);
    if (validationError) {
      console.error('❌ [FileUpload] Validation failed:', validationError);
      setError(validationError);
      return null;
    }

    console.log('✅ [FileUpload] File validation passed');
    setUploading(true);

    try {
      // Simulate upload progress (since fetch doesn't provide real progress)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 100);

      console.log('📤 [FileUpload] Calling API service...');
      const response = await ApiService.uploadPDF(file);

      console.log('✅ [FileUpload] Upload successful:', {
        fileId: response.file_id,
        filename: response.filename,
        fileSize: response.file_size,
        metadata: response.metadata,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      // Keep progress at 100% for a moment before clearing
      setTimeout(() => {
        setUploadProgress(0);
        setUploading(false);
      }, 500);

      return response;
    } catch (err) {
      console.error('❌ [FileUpload] Upload failed:', {
        error: err,
        message: err instanceof Error ? err.message : 'Upload failed',
        stack: err instanceof Error ? err.stack : undefined,
      });
      setError(err instanceof Error ? err.message : 'Upload failed');
      setUploading(false);
      setUploadProgress(0);
      return null;
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    uploading,
    uploadProgress,
    error,
    uploadFile,
    clearError,
  };
};
