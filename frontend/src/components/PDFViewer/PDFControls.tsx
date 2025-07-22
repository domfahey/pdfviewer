import React, { useState } from 'react';
import {
  Toolbar,
  Box,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
  ToggleButton,
  ToggleButtonGroup,
  Divider,
  Collapse,
  InputAdornment,
  Paper,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  NavigateBefore as NavigateBeforeIcon,
  NavigateNext as NavigateNextIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon,
  KeyboardArrowDown as KeyboardArrowDownIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Search as SearchIcon,
  ViewList as ViewListIcon,
  Info as InfoIcon,
  RotateRight as RotateRightIcon,
  Close as CloseIcon,
  FitScreen as FitScreenIcon,
  AspectRatio as AspectRatioIcon,
  CropLandscape as CropLandscapeIcon,
  PictureAsPdf as PictureAsPdfIcon,
  Article as ArticleIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';

interface FitMode {
  mode: 'width' | 'height' | 'page' | 'custom';
  scale?: number;
}

interface PDFControlsProps {
  currentPage: number;
  totalPages: number;
  scale: number;
  fitMode: FitMode;
  viewMode: 'original' | 'digital';
  onPageChange: (page: number) => void;
  onScaleChange: (scale: number) => void;
  onFitModeChange: (fitMode: FitMode) => void;
  onViewModeChange: (mode: 'original' | 'digital') => void;
  onPreviousPage: () => void;
  onNextPage: () => void;
  onToggleThumbnails?: () => void;
  onToggleBookmarks?: () => void;
  onToggleExtractedFields?: () => void;
  onSearch?: (query: string) => void;
  onSearchNext?: () => void;
  onSearchPrevious?: () => void;
  onClearSearch?: () => void;
  searchMatches?: number;
  currentSearchMatch?: number;
  isSearching?: boolean;
  onRotate?: (degrees: number) => void;
  className?: string;
  showAdvanced?: boolean;
}

export const PDFControls: React.FC<PDFControlsProps> = ({
  currentPage,
  totalPages,
  scale,
  fitMode,
  viewMode,
  onPageChange,
  onScaleChange,
  onFitModeChange,
  onViewModeChange,
  onPreviousPage,
  onNextPage,
  onToggleThumbnails,
  onToggleBookmarks,
  onToggleExtractedFields,
  onSearch,
  onSearchNext,
  onSearchPrevious,
  onClearSearch,
  searchMatches = 0,
  currentSearchMatch = 0,
  isSearching = false,
  onRotate,
  showAdvanced = true,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearchBar, setShowSearchBar] = useState(false);
  const handlePageInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const pageNumber = parseInt(event.target.value, 10);
    if (!isNaN(pageNumber) && pageNumber >= 1 && pageNumber <= totalPages) {
      onPageChange(pageNumber);
    }
  };

  const handlePageInputKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      const target = event.target as HTMLInputElement;
      const pageNumber = parseInt(target.value, 10);
      if (!isNaN(pageNumber) && pageNumber >= 1 && pageNumber <= totalPages) {
        onPageChange(pageNumber);
      }
    }
  };

  const handleScaleChange = (newScale: number) => {
    onScaleChange(newScale);
    onFitModeChange({ mode: 'custom', scale: newScale });
  };

  const handleFitModeChange = (mode: 'width' | 'height' | 'page') => {
    onFitModeChange({ mode });
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSearch && searchQuery.trim()) {
      onSearch(searchQuery.trim());
    }
  };

  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const scaleOptions = [
    { value: 0.25, label: '25%' },
    { value: 0.5, label: '50%' },
    { value: 0.75, label: '75%' },
    { value: 1.0, label: '100%' },
    { value: 1.25, label: '125%' },
    { value: 1.5, label: '150%' },
    { value: 2.0, label: '200%' },
    { value: 3.0, label: '300%' },
    { value: 4.0, label: '400%' },
  ];

  return (
    <Paper
      elevation={1}
      sx={{
        borderRadius: 0,
        position: 'sticky',
        top: 0,
        zIndex: 1000,
        backgroundColor: 'background.paper',
      }}
    >
      {/* Compact Material Toolbar */}
      <Toolbar variant="dense" sx={{ gap: 1, flexWrap: 'wrap', minHeight: 40, py: 0.5 }}>
        {/* View Mode Toggle */}
        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={(_, value) => value && onViewModeChange(value)}
          size="small"
          sx={{ height: 32 }}
        >
          <ToggleButton value="original" aria-label="original pdf view" sx={{ px: 1.5, gap: 0.5 }}>
            <PictureAsPdfIcon fontSize="small" />
            <Typography variant="caption" sx={{ fontWeight: 500 }}>
              Original
            </Typography>
          </ToggleButton>
          <ToggleButton
            value="digital"
            aria-label="digital markdown view"
            sx={{ px: 1.5, gap: 0.5 }}
          >
            <ArticleIcon fontSize="small" />
            <Typography variant="caption" sx={{ fontWeight: 500 }}>
              Digital
            </Typography>
          </ToggleButton>
        </ToggleButtonGroup>

        <Divider orientation="vertical" flexItem />

        {/* Compact Page Navigation */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Tooltip title="Previous page">
            <span>
              <IconButton onClick={onPreviousPage} disabled={currentPage <= 1} size="small">
                <NavigateBeforeIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              Page
            </Typography>
            <TextField
              type="number"
              value={currentPage}
              onChange={handlePageInputChange}
              onKeyPress={handlePageInputKeyPress}
              size="small"
              sx={{ width: 60 }}
              inputProps={{
                min: 1,
                max: totalPages,
                style: { textAlign: 'center', fontSize: '0.75rem', padding: '4px 6px' },
              }}
            />
            <Typography variant="caption" color="text.secondary">
              of {totalPages}
            </Typography>
          </Box>

          <Tooltip title="Next page">
            <span>
              <IconButton onClick={onNextPage} disabled={currentPage >= totalPages} size="small">
                <NavigateNextIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        </Box>

        <Divider orientation="vertical" flexItem />

        {/* Compact Zoom Controls */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Tooltip title="Zoom out">
            <IconButton
              onClick={() => handleScaleChange(Math.max(0.25, scale - 0.25))}
              size="small"
            >
              <ZoomOutIcon fontSize="small" />
            </IconButton>
          </Tooltip>

          <FormControl size="small" sx={{ minWidth: 80 }}>
            <Select
              value={scale}
              onChange={e => handleScaleChange(Number(e.target.value))}
              displayEmpty
              sx={{ fontSize: '0.75rem', height: 32 }}
              renderValue={value => {
                const option = scaleOptions.find(opt => opt.value === value);
                return option ? option.label : `${Math.round(value * 100)}%`;
              }}
            >
              {scaleOptions.map(option => (
                <MenuItem key={option.value} value={option.value} sx={{ fontSize: '0.75rem' }}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Tooltip title="Zoom in">
            <IconButton onClick={() => handleScaleChange(Math.min(5.0, scale + 0.25))} size="small">
              <ZoomInIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>

        <Divider orientation="vertical" flexItem />

        {/* Compact Fit Mode Toggle Buttons */}
        <ToggleButtonGroup
          value={fitMode.mode}
          exclusive
          onChange={(_, value) => value && handleFitModeChange(value)}
          size="small"
          sx={{ height: 32 }}
        >
          <ToggleButton value="width" aria-label="fit width" sx={{ px: 1 }}>
            <Tooltip title="Fit to width">
              <CropLandscapeIcon fontSize="small" />
            </Tooltip>
          </ToggleButton>
          <ToggleButton value="height" aria-label="fit height" sx={{ px: 1 }}>
            <Tooltip title="Fit to height">
              <AspectRatioIcon fontSize="small" />
            </Tooltip>
          </ToggleButton>
          <ToggleButton value="page" aria-label="fit page" sx={{ px: 1 }}>
            <Tooltip title="Fit to page">
              <FitScreenIcon fontSize="small" />
            </Tooltip>
          </ToggleButton>
        </ToggleButtonGroup>

        <Box sx={{ flexGrow: 1 }} />

        {/* Advanced Tools */}
        {showAdvanced && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Search in document">
              <IconButton
                onClick={() => setShowSearchBar(!showSearchBar)}
                color={showSearchBar ? 'primary' : 'default'}
                size="small"
              >
                <SearchIcon />
              </IconButton>
            </Tooltip>

            {onToggleThumbnails && (
              <Tooltip title="Toggle thumbnails">
                <IconButton onClick={onToggleThumbnails} size="small">
                  <ViewListIcon />
                </IconButton>
              </Tooltip>
            )}

            {onToggleBookmarks && (
              <Tooltip title="Document info">
                <IconButton onClick={onToggleBookmarks} size="small">
                  <InfoIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {onToggleExtractedFields && (
              <Tooltip title="Extracted fields">
                <IconButton onClick={onToggleExtractedFields} size="small">
                  <DescriptionIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}

            {onRotate && (
              <Tooltip title="Rotate 90 degrees">
                <IconButton onClick={() => onRotate(90)} size="small">
                  <RotateRightIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        )}
      </Toolbar>

      {/* Material Search Bar */}
      <Collapse in={showSearchBar && !!onSearch}>
        <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
          <Box
            component="form"
            onSubmit={handleSearch}
            sx={{ display: 'flex', gap: 1, alignItems: 'center' }}
          >
            <TextField
              fullWidth
              size="small"
              value={searchQuery}
              onChange={handleSearchInputChange}
              placeholder="Search in document..."
              disabled={isSearching}
              InputProps={{
                startAdornment: searchMatches > 0 && (
                  <InputAdornment position="start">
                    <Typography variant="caption" color="text.secondary">
                      {currentSearchMatch + 1} of {searchMatches}
                    </Typography>
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton type="submit" size="small" edge="end" disabled={isSearching}>
                      <SearchIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            {searchMatches > 0 && (
              <>
                <Tooltip title="Previous match (Shift+F3)">
                  <IconButton onClick={onSearchPrevious} size="small" disabled={searchMatches <= 1}>
                    <KeyboardArrowUpIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Next match (F3)">
                  <IconButton onClick={onSearchNext} size="small" disabled={searchMatches <= 1}>
                    <KeyboardArrowDownIcon />
                  </IconButton>
                </Tooltip>
              </>
            )}
            <Tooltip title="Clear search">
              <IconButton
                onClick={() => {
                  setSearchQuery('');
                  setShowSearchBar(false);
                  if (onClearSearch) onClearSearch();
                }}
                size="small"
              >
                <CloseIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Collapse>
    </Paper>
  );
};
