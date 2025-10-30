import { useState } from 'react';
import {
  Container,
  Box,
  Fab,
  Alert,
  Snackbar,
  IconButton,
  Card,
  CardContent,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Close as CloseIcon,
  Visibility as VisibilityIcon,
  Speed as SpeedIcon,
  TouchApp as TouchAppIcon,
} from '@mui/icons-material';
import { FileUpload } from './components/Upload/FileUpload';
import { PDFViewer } from './components/PDFViewer/PDFViewer';
import { TestPDFLoader } from './components/TestPDFLoader';
import { ApiService } from './services/api';
import type { PDFUploadResponse } from './types/pdf.types';
import { devLog } from './utils/devLogger';

function App() {
  const [uploadedFile, setUploadedFile] = useState<PDFUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUploadSuccess = (response: PDFUploadResponse) => {
    devLog('🎉 [App] Upload success callback triggered:', {
      fileId: response.file_id,
      filename: response.filename,
      timestamp: new Date().toISOString(),
    });
    setUploadedFile(response);
    setError(null);
  };

  const handleNewUpload = () => {
    setUploadedFile(null);
    setError(null);
  };

  const getPDFUrl = (fileId: string) => {
    return ApiService.getPDFUrl(fileId);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, bgcolor: 'background.default' }}>
        {!uploadedFile ? (
          /* Upload Section */
          <Container maxWidth="lg" sx={{ py: 8 }}>
            <Box textAlign="center" mb={6}>
              <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 300 }}>
                Upload a PDF to get started
              </Typography>
              <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
                Upload your PDF document to view it with our modern viewer. Supports text selection,
                annotations, and interactive elements.
              </Typography>
            </Box>

            <FileUpload onUploadSuccess={handleUploadSuccess} />

            {/* Test PDF Loader */}
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
              <TestPDFLoader onLoadSuccess={handleUploadSuccess} />
            </Box>

            {/* Features Cards */}
            <Box mt={8}>
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: { xs: 'column', md: 'row' },
                  gap: 4,
                  justifyContent: 'center',
                }}
              >
                <Box sx={{ flex: { md: '0 1 400px' } }}>
                  <Card elevation={2} sx={{ height: '100%', textAlign: 'center' }}>
                    <CardContent sx={{ p: 4 }}>
                      <Box
                        sx={{
                          width: 64,
                          height: 64,
                          borderRadius: 2,
                          bgcolor: 'primary.light',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mx: 'auto',
                          mb: 3,
                        }}
                      >
                        <VisibilityIcon sx={{ fontSize: 32, color: 'primary.main' }} />
                      </Box>
                      <Typography variant="h6" gutterBottom>
                        High-Quality Rendering
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Crystal clear PDF rendering with PDF.js technology
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>

                <Box sx={{ flex: { md: '0 1 400px' } }}>
                  <Card elevation={2} sx={{ height: '100%', textAlign: 'center' }}>
                    <CardContent sx={{ p: 4 }}>
                      <Box
                        sx={{
                          width: 64,
                          height: 64,
                          borderRadius: 2,
                          bgcolor: 'success.light',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mx: 'auto',
                          mb: 3,
                        }}
                      >
                        <TouchAppIcon sx={{ fontSize: 32, color: 'success.main' }} />
                      </Box>
                      <Typography variant="h6" gutterBottom>
                        Interactive Elements
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Support for annotations, links, and form fields
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>

                <Box sx={{ flex: { md: '0 1 400px' } }}>
                  <Card elevation={2} sx={{ height: '100%', textAlign: 'center' }}>
                    <CardContent sx={{ p: 4 }}>
                      <Box
                        sx={{
                          width: 64,
                          height: 64,
                          borderRadius: 2,
                          bgcolor: 'secondary.light',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mx: 'auto',
                          mb: 3,
                        }}
                      >
                        <SpeedIcon sx={{ fontSize: 32, color: 'secondary.main' }} />
                      </Box>
                      <Typography variant="h6" gutterBottom>
                        Performance Optimized
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Virtual scrolling and optimized rendering for large documents
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
              </Box>
            </Box>
          </Container>
        ) : (
          /* PDF Viewer Section */
          <Box sx={{ flex: 1, minHeight: '100vh' }}>
            <PDFViewer fileUrl={getPDFUrl(uploadedFile.file_id)} metadata={uploadedFile.metadata} />
          </Box>
        )}
      </Box>

      {/* Floating Action Button for New Upload */}
      {uploadedFile && (
        <Fab
          color="primary"
          aria-label="upload new PDF"
          onClick={handleNewUpload}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
          }}
        >
          <AddIcon />
        </Fab>
      )}

      {/* Material Snackbar for Errors */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setError(null)}
          severity="error"
          variant="filled"
          action={
            <IconButton
              size="small"
              aria-label="close"
              color="inherit"
              onClick={() => setError(null)}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          }
        >
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default App;
