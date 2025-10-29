import React, { useState, useRef, useCallback } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Alert,
  IconButton,
  alpha,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Close as CloseIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useFileUpload } from '../../hooks/useFileUpload';
import type { PDFUploadResponse } from '../../types/pdf.types';

interface FileUploadProps {
  onUploadSuccess: (response: PDFUploadResponse) => void;
  className?: string;
}

/**
 * File upload component with drag-and-drop support.
 * Displays upload progress and handles errors gracefully.
 *
 * @param props - Component properties
 * @param props.onUploadSuccess - Callback function called when upload succeeds
 * @param props.className - Optional CSS class name for styling
 */
export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const { uploading, uploadProgress, error, uploadFile, clearError } = useFileUpload();
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = useCallback(
    async (file: File) => {
      clearError();
      const response = await uploadFile(file);
      if (response) {
        onUploadSuccess(response);
      }
    },
    [uploadFile, onUploadSuccess, clearError]
  );

  const handleFileInputChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file) {
        handleFileSelect(file);
      }
    },
    [handleFileSelect]
  );

  const handleDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDragOver(false);

      const files = event.dataTransfer.files;
      if (files.length > 0) {
        handleFileSelect(files[0]);
      }
    },
    [handleFileSelect]
  );

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  return (
    <Box sx={{ width: '100%', maxWidth: 600, mx: 'auto' }}>
      <Card
        elevation={isDragOver ? 4 : 2}
        sx={{
          cursor: uploading ? 'not-allowed' : 'pointer',
          transition: 'all 0.3s ease-in-out',
          border: 2,
          borderStyle: 'dashed',
          borderColor: isDragOver ? 'primary.main' : 'grey.300',
          bgcolor: isDragOver ? alpha('#1976d2', 0.04) : uploading ? 'grey.50' : 'background.paper',
          opacity: uploading ? 0.7 : 1,
          '&:hover': {
            borderColor: uploading ? 'grey.300' : 'primary.light',
            bgcolor: uploading ? 'grey.50' : alpha('#1976d2', 0.02),
            elevation: uploading ? 2 : 3,
          },
        }}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
      >
        <CardContent sx={{ p: 6, textAlign: 'center' }}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileInputChange}
            style={{ display: 'none' }}
            disabled={uploading}
          />

          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
            {/* Upload Icon */}
            <CloudUploadIcon
              sx={{
                fontSize: 64,
                color: isDragOver ? 'primary.main' : 'grey.400',
                transition: 'color 0.3s ease-in-out',
              }}
            />

            {uploading ? (
              <Box sx={{ width: '100%', maxWidth: 300 }}>
                <Typography variant="body1" sx={{ mb: 2, fontWeight: 500 }}>
                  Uploading...
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={uploadProgress}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    mb: 1,
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  {uploadProgress}%
                </Typography>
              </Box>
            ) : (
              <Box>
                <Typography variant="h6" sx={{ mb: 1, fontWeight: 500 }}>
                  Drop your PDF here
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  or click to browse files
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Maximum file size: 50MB
                </Typography>
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>

      {error && (
        <Alert
          severity="error"
          sx={{ mt: 2 }}
          action={
            <IconButton aria-label="close" color="inherit" size="small" onClick={clearError}>
              <CloseIcon fontSize="inherit" />
            </IconButton>
          }
          icon={<ErrorIcon fontSize="inherit" />}
        >
          <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
            Upload Error
          </Typography>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      )}
    </Box>
  );
};
