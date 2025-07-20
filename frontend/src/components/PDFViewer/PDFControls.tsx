import React from 'react';

interface PDFControlsProps {
  currentPage: number;
  totalPages: number;
  scale: number;
  onPageChange: (page: number) => void;
  onScaleChange: (scale: number) => void;
  onPreviousPage: () => void;
  onNextPage: () => void;
  className?: string;
}

export const PDFControls: React.FC<PDFControlsProps> = ({
  currentPage,
  totalPages,
  scale,
  onPageChange,
  onScaleChange,
  onPreviousPage,
  onNextPage,
  className = '',
}) => {
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
  };

  const scaleOptions = [
    { value: 0.5, label: '50%' },
    { value: 0.75, label: '75%' },
    { value: 1.0, label: '100%' },
    { value: 1.25, label: '125%' },
    { value: 1.5, label: '150%' },
    { value: 2.0, label: '200%' },
  ];

  return (
    <div className={`flex items-center justify-between p-4 bg-gray-100 border-b ${className}`}>
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
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>

      {/* Fit Options */}
      <div className="flex items-center space-x-2">
        <button
          onClick={() => handleScaleChange(1.0)}
          className="px-3 py-1 text-sm bg-white border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
        >
          Fit Width
        </button>
        <button
          onClick={() => handleScaleChange(0.75)}
          className="px-3 py-1 text-sm bg-white border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
        >
          Fit Page
        </button>
      </div>
    </div>
  );
};
