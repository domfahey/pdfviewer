import React, { useState } from 'react';
import {
  Box,
  Button,
  Menu,
  MenuItem,
  CircularProgress,
  Alert,
  Snackbar,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
} from '@mui/material';
import {
  Science as ScienceIcon,
  CloudDownload as CloudDownloadIcon,
  Description as DescriptionIcon,
  Image as ImageIcon,
} from '@mui/icons-material';
import type { PDFUploadResponse } from '../types/pdf.types';

interface TestPDF {
  name: string;
  url: string;
  description: string;
  icon: React.ReactNode;
}

const TEST_PDFS: TestPDF[] = [
  {
    name: 'EPA Sample Letter',
    url: 'https://19january2021snapshot.epa.gov/sites/static/files/2016-02/documents/epa_sample_letter_sent_to_commissioners_dated_february_29_2015.pdf',
    description: 'Official EPA document with text content',
    icon: <DescriptionIcon />,
  },
  {
    name: 'Image-based PDF',
    url: 'https://nlsblog.org/wp-content/uploads/2020/06/image-based-pdf-sample.pdf',
    description: 'Scanned document without text layer',
    icon: <ImageIcon />,
  },
  {
    name: 'Anyline Sample Book',
    url: 'https://anyline.com/app/uploads/2022/03/anyline-sample-scan-book.pdf',
    description: 'Multi-page document with mixed content',
    icon: <DescriptionIcon />,
  },
  {
    name: 'NHTSA Form',
    url: 'https://www.nhtsa.gov/sites/nhtsa.gov/files/documents/mo_par_rev01_2012.pdf',
    description: 'Government form with fillable fields',
    icon: <DescriptionIcon />,
  },
];

interface TestPDFLoaderProps {
  onLoadSuccess?: (response: PDFUploadResponse) => void;
}

export const TestPDFLoader: React.FC<TestPDFLoaderProps> = ({ onLoadSuccess }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLoadPDF = async (testPDF: TestPDF) => {
    handleClose();
    setLoading(true);
    setError(null);

    try {
      // Call the backend API to load PDF from URL
      const response = await fetch('http://localhost:8000/api/load-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: testPDF.url }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to load PDF');
      }

      const data: PDFUploadResponse = await response.json();

      // Call the parent's callback if provided
      if (onLoadSuccess) {
        onLoadSuccess(data);
      }

      setSuccess(`Successfully loaded: ${testPDF.name}`);
    } catch (error) {
      console.error('Error loading test PDF:', error);
      setError(error instanceof Error ? error.message : 'Failed to load PDF');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Button
        variant="outlined"
        startIcon={loading ? <CircularProgress size={20} /> : <ScienceIcon />}
        onClick={handleClick}
        disabled={loading}
        sx={{
          borderColor: 'primary.light',
          color: 'primary.main',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'primary.50',
          },
        }}
      >
        Load Test PDF
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        PaperProps={{
          sx: { minWidth: 300 },
        }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="subtitle2" color="text.secondary">
            Sample PDFs for Testing
          </Typography>
        </Box>
        <Divider />

        {TEST_PDFS.map((testPDF, index) => (
          <MenuItem key={index} onClick={() => handleLoadPDF(testPDF)} sx={{ py: 1.5 }}>
            <ListItemIcon>{testPDF.icon}</ListItemIcon>
            <ListItemText
              primary={testPDF.name}
              secondary={testPDF.description}
              secondaryTypographyProps={{
                variant: 'caption',
                color: 'text.secondary',
              }}
            />
          </MenuItem>
        ))}

        <Divider />
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="caption" color="text.secondary">
            <CloudDownloadIcon sx={{ fontSize: 12, mr: 0.5, verticalAlign: 'middle' }} />
            PDFs will be downloaded from external sources
          </Typography>
        </Box>
      </Menu>

      <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError(null)}>
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>

      <Snackbar open={!!success} autoHideDuration={3000} onClose={() => setSuccess(null)}>
        <Alert severity="success" onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      </Snackbar>
    </Box>
  );
};
