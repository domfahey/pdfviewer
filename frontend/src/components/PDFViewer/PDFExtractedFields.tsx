import React from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  Tooltip,
} from '@mui/material';
import {
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  DateRange as DateRangeIcon,
  AttachMoney as MoneyIcon,
  Description as DescriptionIcon,
  TableChart as TableChartIcon,
} from '@mui/icons-material';

interface PDFExtractedFieldsProps {
  isVisible: boolean;
  onClose: () => void;
  width: number;
  onResize: (width: number) => void;
}

export const PDFExtractedFields: React.FC<PDFExtractedFieldsProps> = ({
  isVisible,
  onClose,
  width,
  onResize,
}) => {
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = width;

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = startX - e.clientX;
      const newWidth = Math.min(Math.max(300, startWidth + deltaX), 800);
      onResize(newWidth);
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  if (!isVisible) return null;

  // Mock extracted fields data
  const extractedFields = {
    personal: [
      { label: 'Full Name', value: 'John Smith', confidence: 0.95 },
      { label: 'Email', value: 'john.smith@email.com', confidence: 0.92 },
      { label: 'Phone', value: '+1 (555) 123-4567', confidence: 0.88 },
    ],
    business: [
      { label: 'Company', value: 'Acme Corporation', confidence: 0.97 },
      { label: 'Position', value: 'Senior Manager', confidence: 0.85 },
      { label: 'Department', value: 'Operations', confidence: 0.8 },
    ],
    dates: [
      { label: 'Document Date', value: '2024-01-15', confidence: 0.99 },
      { label: 'Expiry Date', value: '2025-01-15', confidence: 0.93 },
      { label: 'Created Date', value: '2024-01-10', confidence: 0.87 },
    ],
    financial: [
      { label: 'Total Amount', value: '$12,345.67', confidence: 0.96 },
      { label: 'Tax Amount', value: '$1,234.56', confidence: 0.91 },
      { label: 'Net Amount', value: '$11,111.11', confidence: 0.94 },
    ],
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'success';
    if (confidence >= 0.8) return 'warning';
    return 'error';
  };

  const fieldCategories = [
    {
      title: 'Personal Information',
      icon: <PersonIcon fontSize="small" />,
      fields: extractedFields.personal,
    },
    {
      title: 'Business Details',
      icon: <BusinessIcon fontSize="small" />,
      fields: extractedFields.business,
    },
    {
      title: 'Dates',
      icon: <DateRangeIcon fontSize="small" />,
      fields: extractedFields.dates,
    },
    {
      title: 'Financial',
      icon: <MoneyIcon fontSize="small" />,
      fields: extractedFields.financial,
    },
  ];

  return (
    <Box
      sx={{
        width: `${width}px`,
        height: '100%',
        display: 'flex',
        flexDirection: 'row',
        position: 'relative',
      }}
    >
      {/* Resize Handle */}
      <Box
        onMouseDown={handleMouseDown}
        sx={{
          width: 4,
          bgcolor: 'divider',
          cursor: 'col-resize',
          '&:hover': {
            bgcolor: 'primary.main',
          },
          transition: 'background-color 0.2s',
        }}
      />

      {/* Panel Content */}
      <Paper
        elevation={2}
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          bgcolor: 'background.paper',
          borderRadius: 0,
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 2,
            borderBottom: '1px solid',
            borderColor: 'divider',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DescriptionIcon color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 500 }}>
              Extracted Fields
            </Typography>
          </Box>
          <Tooltip title="Close panel">
            <IconButton onClick={onClose} size="small">
              <CloseIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Content */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 1 }}>
          {/* Status Banner */}
          <Box
            sx={{
              mb: 2,
              p: 2,
              bgcolor: 'info.light',
              borderRadius: 1,
              border: '1px dashed',
              borderColor: 'info.main',
            }}
          >
            <Typography variant="body2" color="info.dark" sx={{ fontWeight: 500 }}>
              🚧 Feature Preview
            </Typography>
            <Typography variant="caption" color="info.dark">
              AI-powered field extraction coming soon. This preview shows the planned interface.
            </Typography>
          </Box>

          {/* Field Categories */}
          {fieldCategories.map((category, index) => (
            <Accordion key={index} defaultExpanded sx={{ mb: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {category.icon}
                  <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
                    {category.title}
                  </Typography>
                  <Chip
                    label={category.fields.length}
                    size="small"
                    variant="outlined"
                    sx={{ ml: 'auto' }}
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails sx={{ pt: 0 }}>
                <List dense>
                  {category.fields.map((field, fieldIndex) => (
                    <ListItem key={fieldIndex} sx={{ px: 0, py: 0.5 }}>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              {field.label}
                            </Typography>
                            <Chip
                              label={`${Math.round(field.confidence * 100)}%`}
                              size="small"
                              color={getConfidenceColor(field.confidence)}
                              sx={{ height: 16, fontSize: '0.65rem' }}
                            />
                          </Box>
                        }
                        secondaryTypographyProps={{
                          component: 'div',
                        }}
                        secondary={
                          <TextField
                            value={field.value}
                            size="small"
                            fullWidth
                            variant="outlined"
                            InputProps={{
                              readOnly: true,
                              sx: { fontSize: '0.75rem', bgcolor: 'grey.50' },
                            }}
                            sx={{ mt: 0.5 }}
                          />
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          ))}

          {/* Additional Features Preview */}
          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <TableChartIcon fontSize="small" color="primary" />
              <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
                Coming Soon
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary" component="div">
              • Table extraction and recognition
              <br />
              • Custom field templates
              <br />
              • Export to CSV/JSON
              <br />
              • Field validation rules
              <br />• OCR confidence tuning
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};
