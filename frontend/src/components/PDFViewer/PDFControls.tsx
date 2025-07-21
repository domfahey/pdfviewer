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
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Search as SearchIcon,
  ViewList as ViewListIcon,
  Bookmark as BookmarkIcon,
  RotateRight as RotateRightIcon,
  Close as CloseIcon,
  FitScreen as FitScreenIcon,
  AspectRatio as AspectRatioIcon,
  CropLandscape as CropLandscapeIcon,
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
  onPageChange: (page: number) => void;
  onScaleChange: (scale: number) => void;
  onFitModeChange: (fitMode: FitMode) => void;
  onPreviousPage: () => void;
  onNextPage: () => void;
  onToggleThumbnails?: () => void;
  onToggleBookmarks?: () => void;
  onSearch?: (query: string) => void;
  onRotate?: (degrees: number) => void;
  className?: string;
  showAdvanced?: boolean;
}

export const PDFControls: React.FC<PDFControlsProps> = ({
  currentPage,
  totalPages,
  scale,
  fitMode,
  onPageChange,
  onScaleChange,
  onFitModeChange,
  onPreviousPage,
  onNextPage,
  onToggleThumbnails,
  onToggleBookmarks,
  onSearch,
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
    <Paper elevation={1} sx={{ borderRadius: 0 }}>
      {/* Main Material Toolbar */}
      <Toolbar sx={{ gap: 2, flexWrap: 'wrap', minHeight: 64 }}>
        {/* Page Navigation */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Previous page">
            <span>
              <IconButton onClick={onPreviousPage} disabled={currentPage <= 1} size="small">
                <NavigateBeforeIcon />
              </IconButton>
            </span>
          </Tooltip>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Page
            </Typography>
            <TextField
              type="number"
              value={currentPage}
              onChange={handlePageInputChange}
              onKeyPress={handlePageInputKeyPress}
              size="small"
              sx={{ width: 80 }}
              inputProps={{
                min: 1,
                max: totalPages,
                style: { textAlign: 'center' },
              }}
            />
            <Typography variant="body2" color="text.secondary">
              of {totalPages}
            </Typography>
          </Box>

          <Tooltip title="Next page">
            <span>
              <IconButton onClick={onNextPage} disabled={currentPage >= totalPages} size="small">
                <NavigateNextIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>

        <Divider orientation="vertical" flexItem />

        {/* Zoom Controls */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Zoom out">
            <IconButton
              onClick={() => handleScaleChange(Math.max(0.25, scale - 0.25))}
              size="small"
            >
              <ZoomOutIcon />
            </IconButton>
          </Tooltip>

          <FormControl size="small" sx={{ minWidth: 90 }}>
            <Select
              value={scale}
              onChange={e => handleScaleChange(Number(e.target.value))}
              displayEmpty
              renderValue={value => {
                const option = scaleOptions.find(opt => opt.value === value);
                return option ? option.label : `${Math.round(value * 100)}%`;
              }}
            >
              {scaleOptions.map(option => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Tooltip title="Zoom in">
            <IconButton onClick={() => handleScaleChange(Math.min(5.0, scale + 0.25))} size="small">
              <ZoomInIcon />
            </IconButton>
          </Tooltip>
        </Box>

        <Divider orientation="vertical" flexItem />

        {/* Fit Mode Toggle Buttons */}
        <ToggleButtonGroup
          value={fitMode.mode}
          exclusive
          onChange={(_, value) => value && handleFitModeChange(value)}
          size="small"
        >
          <ToggleButton value="width" aria-label="fit width">
            <Tooltip title="Fit to width">
              <CropLandscapeIcon />
            </Tooltip>
          </ToggleButton>
          <ToggleButton value="height" aria-label="fit height">
            <Tooltip title="Fit to height">
              <AspectRatioIcon />
            </Tooltip>
          </ToggleButton>
          <ToggleButton value="page" aria-label="fit page">
            <Tooltip title="Fit to page">
              <FitScreenIcon />
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
              <Tooltip title="Toggle bookmarks">
                <IconButton onClick={onToggleBookmarks} size="small">
                  <BookmarkIcon />
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
          <Box component="form" onSubmit={handleSearch} sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              size="small"
              value={searchQuery}
              onChange={handleSearchInputChange}
              placeholder="Search in document..."
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton type="submit" size="small" edge="end">
                      <SearchIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            <Tooltip title="Close search">
              <IconButton onClick={() => setShowSearchBar(false)} size="small">
                <CloseIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Collapse>
    </Paper>
  );
};
