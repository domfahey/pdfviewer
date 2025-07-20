import React, { useState } from 'react';

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
  className = '',
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
    <div className={`bg-gray-100 border-b ${className}`}>
      {/* Main Toolbar */}
      <div className="flex items-center justify-between p-4">
        {/* Page Navigation */}
        <div className="flex items-center space-x-2">
          <button
            onClick={onPreviousPage}
            disabled={currentPage <= 1}
            className="p-2 rounded-md bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Previous page"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>

          <div className="flex items-center space-x-1">
            <span className="text-sm text-gray-600">Page</span>
            <input
              type="number"
              min="1"
              max={totalPages}
              value={currentPage}
              onChange={handlePageInputChange}
              onKeyPress={handlePageInputKeyPress}
              className="w-16 px-2 py-1 text-sm border border-gray-300 rounded-md text-center focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-600">of {totalPages}</span>
          </div>

          <button
            onClick={onNextPage}
            disabled={currentPage >= totalPages}
            className="p-2 rounded-md bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Next page"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleScaleChange(Math.max(0.25, scale - 0.25))}
            className="p-2 rounded-md bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
            aria-label="Zoom out"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>

          <select
            value={scale}
            onChange={e => handleScaleChange(parseFloat(e.target.value))}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {scaleOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          <button
            onClick={() => handleScaleChange(Math.min(5.0, scale + 0.25))}
            className="p-2 rounded-md bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
            aria-label="Zoom in"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
          </button>
        </div>

        {/* Fit Options */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleFitModeChange('width')}
            className={`px-3 py-1 text-sm border rounded-md ${
              fitMode.mode === 'width'
                ? 'bg-blue-500 text-white border-blue-500'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            Fit Width
          </button>
          <button
            onClick={() => handleFitModeChange('height')}
            className={`px-3 py-1 text-sm border rounded-md ${
              fitMode.mode === 'height'
                ? 'bg-blue-500 text-white border-blue-500'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            Fit Height
          </button>
          <button
            onClick={() => handleFitModeChange('page')}
            className={`px-3 py-1 text-sm border rounded-md ${
              fitMode.mode === 'page'
                ? 'bg-blue-500 text-white border-blue-500'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            Fit Page
          </button>
        </div>

        {/* Advanced Tools */}
        {showAdvanced && (
          <div className="flex items-center space-x-2">
            {/* Search Toggle */}
            <button
              onClick={() => setShowSearchBar(!showSearchBar)}
              className={`p-2 rounded-md border ${
                showSearchBar
                  ? 'bg-blue-500 text-white border-blue-500'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
              aria-label="Toggle search"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </button>

            {/* Thumbnails Toggle */}
            {onToggleThumbnails && (
              <button
                onClick={onToggleThumbnails}
                className="p-2 rounded-md bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                aria-label="Toggle thumbnails"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 11H5m14-7H5m14 14H5"
                  />
                </svg>
              </button>
            )}

            {/* Bookmarks Toggle */}
            {onToggleBookmarks && (
              <button
                onClick={onToggleBookmarks}
                className="p-2 rounded-md bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                aria-label="Toggle bookmarks"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
                  />
                </svg>
              </button>
            )}

            {/* Rotate */}
            {onRotate && (
              <button
                onClick={() => onRotate(90)}
                className="p-2 rounded-md bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                aria-label="Rotate 90 degrees"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Search Bar */}
      {showSearchBar && onSearch && (
        <div className="px-4 pb-4">
          <form onSubmit={handleSearch} className="flex items-center space-x-2">
            <div className="flex-1 relative">
              <input
                type="text"
                value={searchQuery}
                onChange={handleSearchInputChange}
                placeholder="Search in document..."
                className="w-full px-3 py-2 pr-10 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </button>
            </div>
            <button
              type="button"
              onClick={() => setShowSearchBar(false)}
              className="p-2 text-gray-400 hover:text-gray-600"
              aria-label="Close search"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
