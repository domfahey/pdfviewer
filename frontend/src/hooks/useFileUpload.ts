import { useState, useCallback, useRef, useEffect } from 'react';
import { ApiService } from '../services/api';
import type { PDFUploadResponse } from '../types/pdf.types';
import { devLog, devError } from '../utils/devLogger';

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
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const resetTimeoutRef = useRef<NodeJS.Timeout | null>(null);

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
    devLog('🚀 [FileUpload] Starting upload process:', {
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
      devError('❌ [FileUpload] Validation failed:', validationError);
      setError(validationError);
      return null;
    }

    devLog('✅ [FileUpload] File validation passed');
    setUploading(true);

    try {
      // Simulate upload progress (since fetch doesn't provide real progress)
      progressIntervalRef.current = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            if (progressIntervalRef.current) {
              clearInterval(progressIntervalRef.current);
              progressIntervalRef.current = null;
            }
            return prev;
          }
          return prev + 10;
        });
      }, 100);

      devLog('📤 [FileUpload] Calling API service...');
      const response = await ApiService.uploadPDF(file);

      devLog('✅ [FileUpload] Upload successful:', {
        fileId: response.file_id,
        filename: response.filename,
        fileSize: response.file_size,
        metadata: response.metadata,
      });

      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
      setUploadProgress(100);

      // Keep progress at 100% for a moment before clearing
      resetTimeoutRef.current = setTimeout(() => {
        setUploadProgress(0);
        setUploading(false);
        resetTimeoutRef.current = null;
      }, 500);

      return response;
    } catch (error) {
      devError('❌ [FileUpload] Upload failed:', {
        error: error,
        message: error instanceof Error ? error.message : 'Upload failed',
        stack: error instanceof Error ? error.stack : undefined,
      });
      setError(error instanceof Error ? error.message : 'Upload failed');
      setUploading(false);
      setUploadProgress(0);
      return null;
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Cleanup on unmount - clear any active timers
  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
      if (resetTimeoutRef.current) {
        clearTimeout(resetTimeoutRef.current);
      }
    };
  }, []);

  return {
    uploading,
    uploadProgress,
    error,
    uploadFile,
    clearError,
  };
};
