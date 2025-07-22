import React, { useState } from 'react';
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
  ToggleButton,
  ToggleButtonGroup,
  Card,
  CardContent,
  LinearProgress,
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
  CheckCircle as CheckCircleIcon,
  SwapHoriz as SwapHorizIcon,
  Cancel as CancelIcon,
  Remove as RemoveIcon,
  Compare as CompareIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';

interface ExtractedField {
  label: string;
  value: string;
  confidence: number;
  groundTruth?: string;
  accuracy?: 'exact' | 'similar' | 'different' | 'no-truth';
}

interface FieldCategory {
  title: string;
  icon: React.ReactNode;
  fields: ExtractedField[];
}

interface PDFExtractedFieldsProps {
  isVisible: boolean;
  onClose: () => void;
  width: number;
  onResize: (width: number) => void;
}

// Mock extracted fields data with ground truth
// Defined outside component to avoid recreating on every render
const MOCK_EXTRACTED_FIELDS = {
  personal: [
    {
      label: 'Full Name',
      value: 'John Smith',
      confidence: 0.95,
      groundTruth: 'John Smith',
      accuracy: 'exact' as const,
    },
    {
      label: 'Email',
      value: 'john.smith@email.com',
      confidence: 0.92,
      groundTruth: 'j.smith@email.com',
      accuracy: 'different' as const,
    },
    {
      label: 'Phone',
      value: '+1 (555) 123-4567',
      confidence: 0.88,
      groundTruth: '5551234567',
      accuracy: 'similar' as const,
    },
  ],
  business: [
    {
      label: 'Company',
      value: 'Acme Corporation',
      confidence: 0.97,
      groundTruth: 'ACME Corporation',
      accuracy: 'similar' as const,
    },
    {
      label: 'Position',
      value: 'Senior Manager',
      confidence: 0.85,
      groundTruth: 'Senior Manager',
      accuracy: 'exact' as const,
    },
    {
      label: 'Department',
      value: 'Operations',
      confidence: 0.8,
      // No ground truth for this field
      accuracy: 'no-truth' as const,
    },
  ],
  dates: [
    {
      label: 'Document Date',
      value: '2024-01-15',
      confidence: 0.99,
      groundTruth: '01/15/2024',
      accuracy: 'similar' as const,
    },
    {
      label: 'Expiry Date',
      value: '2025-01-15',
      confidence: 0.93,
      groundTruth: '2025-01-15',
      accuracy: 'exact' as const,
    },
    {
      label: 'Created Date',
      value: '2024-01-10',
      confidence: 0.87,
      groundTruth: '2024-01-12',
      accuracy: 'different' as const,
    },
  ],
  financial: [
    {
      label: 'Total Amount',
      value: '$12,345.67',
      confidence: 0.96,
      groundTruth: '12345.67',
      accuracy: 'similar' as const,
    },
    {
      label: 'Tax Amount',
      value: '$1,234.56',
      confidence: 0.91,
      groundTruth: '$1,234.56',
      accuracy: 'exact' as const,
    },
    {
      label: 'Net Amount',
      value: '$11,111.11',
      confidence: 0.94,
      groundTruth: '$11,211.11',
      accuracy: 'different' as const,
    },
  ],
};

export const PDFExtractedFields: React.FC<PDFExtractedFieldsProps> = ({
  isVisible,
  onClose,
  width,
  onResize,
}) => {
  const [viewMode, setViewMode] = useState<'extraction' | 'comparison'>('extraction');

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

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'success';
    if (confidence >= 0.8) return 'warning';
    return 'error';
  };

  const getAccuracyIcon = (accuracy?: ExtractedField['accuracy']) => {
    switch (accuracy) {
      case 'exact':
        return <CheckCircleIcon sx={{ color: 'success.main', fontSize: 20 }} />;
      case 'similar':
        return <SwapHorizIcon sx={{ color: 'warning.main', fontSize: 20 }} />;
      case 'different':
        return <CancelIcon sx={{ color: 'error.main', fontSize: 20 }} />;
      case 'no-truth':
      default:
        return <RemoveIcon sx={{ color: 'text.disabled', fontSize: 20 }} />;
    }
  };

  const getAccuracyLabel = (accuracy?: ExtractedField['accuracy']) => {
    switch (accuracy) {
      case 'exact':
        return 'Exact Match';
      case 'similar':
        return 'Similar';
      case 'different':
        return 'Different';
      case 'no-truth':
      default:
        return 'No Ground Truth';
    }
  };

  const getAccuracyColor = (accuracy?: ExtractedField['accuracy']) => {
    switch (accuracy) {
      case 'exact':
        return 'success.main';
      case 'similar':
        return 'warning.main';
      case 'different':
        return 'error.main';
      case 'no-truth':
      default:
        return 'text.disabled';
    }
  };

  // Calculate accuracy metrics
  const calculateAccuracyMetrics = () => {
    const allFields = [
      ...MOCK_EXTRACTED_FIELDS.personal,
      ...MOCK_EXTRACTED_FIELDS.business,
      ...MOCK_EXTRACTED_FIELDS.dates,
      ...MOCK_EXTRACTED_FIELDS.financial,
    ];

    const withGroundTruth = allFields.filter(f => f.accuracy !== 'no-truth');
    const exact = withGroundTruth.filter(f => f.accuracy === 'exact').length;
    const similar = withGroundTruth.filter(f => f.accuracy === 'similar').length;
    const different = withGroundTruth.filter(f => f.accuracy === 'different').length;
    const total = withGroundTruth.length;

    const accuracy = total > 0 ? ((exact + similar * 0.5) / total) * 100 : 0;

    return { exact, similar, different, total, accuracy };
  };

  const fieldCategories: FieldCategory[] = [
    {
      title: 'Personal Information',
      icon: <PersonIcon fontSize="small" />,
      fields: MOCK_EXTRACTED_FIELDS.personal,
    },
    {
      title: 'Business Details',
      icon: <BusinessIcon fontSize="small" />,
      fields: MOCK_EXTRACTED_FIELDS.business,
    },
    {
      title: 'Dates',
      icon: <DateRangeIcon fontSize="small" />,
      fields: MOCK_EXTRACTED_FIELDS.dates,
    },
    {
      title: 'Financial',
      icon: <MoneyIcon fontSize="small" />,
      fields: MOCK_EXTRACTED_FIELDS.financial,
    },
  ];

  const metrics = calculateAccuracyMetrics();

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
            flexDirection: 'column',
            gap: 2,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
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

          {/* View Mode Toggle */}
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(_, newMode) => newMode && setViewMode(newMode)}
            size="small"
            fullWidth
          >
            <ToggleButton value="extraction">
              <AssignmentIcon sx={{ mr: 1, fontSize: 20 }} />
              Extraction Only
            </ToggleButton>
            <ToggleButton value="comparison">
              <CompareIcon sx={{ mr: 1, fontSize: 20 }} />
              Ground Truth Comparison
            </ToggleButton>
          </ToggleButtonGroup>
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

          {/* Accuracy Metrics Card - Only show in comparison mode */}
          {viewMode === 'comparison' && (
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 500 }}>
                  Accuracy Metrics
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" color="text.secondary">
                      Overall Accuracy
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {metrics.accuracy.toFixed(1)}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={metrics.accuracy}
                    sx={{ height: 8, borderRadius: 1 }}
                    color={
                      metrics.accuracy >= 80
                        ? 'success'
                        : metrics.accuracy >= 60
                          ? 'warning'
                          : 'error'
                    }
                  />
                </Box>
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <CheckCircleIcon sx={{ color: 'success.main', fontSize: 16 }} />
                    <Typography variant="caption">
                      Exact: {metrics.exact}/{metrics.total}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <SwapHorizIcon sx={{ color: 'warning.main', fontSize: 16 }} />
                    <Typography variant="caption">
                      Similar: {metrics.similar}/{metrics.total}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <CancelIcon sx={{ color: 'error.main', fontSize: 16 }} />
                    <Typography variant="caption">
                      Different: {metrics.different}/{metrics.total}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <RemoveIcon sx={{ color: 'text.disabled', fontSize: 16 }} />
                    <Typography variant="caption">
                      No Truth:{' '}
                      {fieldCategories.reduce(
                        (acc, cat) =>
                          acc + cat.fields.filter(f => f.accuracy === 'no-truth').length,
                        0
                      )}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          )}

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
                          viewMode === 'extraction' ? (
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
                          ) : (
                            <Box sx={{ mt: 0.5 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                <Box sx={{ flex: 1 }}>
                                  <Typography
                                    variant="caption"
                                    color="text.secondary"
                                    sx={{ display: 'block', mb: 0.5 }}
                                  >
                                    Extracted Value
                                  </Typography>
                                  <TextField
                                    value={field.value}
                                    size="small"
                                    fullWidth
                                    variant="outlined"
                                    InputProps={{
                                      readOnly: true,
                                      sx: { fontSize: '0.75rem', bgcolor: 'grey.50' },
                                    }}
                                  />
                                </Box>
                                <Box
                                  sx={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    mt: 2,
                                  }}
                                >
                                  {getAccuracyIcon(field.accuracy)}
                                  <Typography
                                    variant="caption"
                                    color={getAccuracyColor(field.accuracy)}
                                  >
                                    {getAccuracyLabel(field.accuracy)}
                                  </Typography>
                                </Box>
                              </Box>
                              {field.groundTruth && (
                                <Box>
                                  <Typography
                                    variant="caption"
                                    color="text.secondary"
                                    sx={{ display: 'block', mb: 0.5 }}
                                  >
                                    Ground Truth
                                  </Typography>
                                  <TextField
                                    value={field.groundTruth}
                                    size="small"
                                    fullWidth
                                    variant="outlined"
                                    InputProps={{
                                      readOnly: true,
                                      sx: {
                                        fontSize: '0.75rem',
                                        bgcolor:
                                          field.accuracy === 'exact'
                                            ? 'success.lighter'
                                            : field.accuracy === 'similar'
                                              ? 'warning.lighter'
                                              : 'error.lighter',
                                        borderColor: getAccuracyColor(field.accuracy),
                                      },
                                    }}
                                  />
                                </Box>
                              )}
                            </Box>
                          )
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
              • Export comparison results to CSV/JSON
              <br />
              • Field validation rules
              <br />
              • Ground truth batch upload
              <br />
              • Similarity threshold configuration
              <br />• OCR confidence tuning
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};
