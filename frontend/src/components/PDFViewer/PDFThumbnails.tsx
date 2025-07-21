import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as pdfjsLib from 'pdfjs-dist';

interface PDFThumbnailsProps {
  pdfDocument: pdfjsLib.PDFDocumentProxy | null;
  currentPage: number;
  onPageSelect: (page: number) => void;
  isVisible: boolean;
  className?: string;
}

interface ThumbnailData {
  pageNumber: number;
  canvas: HTMLCanvasElement | null;
  isLoading: boolean;
}

export const PDFThumbnails: React.FC<PDFThumbnailsProps> = ({
  pdfDocument,
  currentPage,
  onPageSelect,
  isVisible,
  className = '',
}) => {
  const [thumbnails, setThumbnails] = useState<ThumbnailData[]>([]);
  const thumbnailRefs = useRef<(HTMLDivElement | null)[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  const generateThumbnails = useCallback(async () => {
    if (!pdfDocument) return;

    setIsGenerating(true);
    const newThumbnails: ThumbnailData[] = [];

    // Initialize thumbnail data
    for (let i = 1; i <= pdfDocument.numPages; i++) {
      newThumbnails.push({
        pageNumber: i,
        canvas: null,
        isLoading: true,
      });
    }

    setThumbnails([...newThumbnails]);

    // Generate thumbnails asynchronously
    const generateThumbnail = async (pageNumber: number) => {
      try {
        const page = await pdfDocument.getPage(pageNumber);
        const viewport = page.getViewport({ scale: 0.2 }); // Small scale for thumbnails

        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');

        if (!context) return;

        canvas.height = viewport.height;
        canvas.width = viewport.width;

        const renderContext = {
          canvasContext: context,
          viewport: viewport,
        };

        await page.render(renderContext).promise;

        setThumbnails(prev =>
          prev.map(thumb =>
            thumb.pageNumber === pageNumber ? { ...thumb, canvas, isLoading: false } : thumb
          )
        );
      } catch (error) {
        console.error(`Error generating thumbnail for page ${pageNumber}:`, error);
        setThumbnails(prev =>
          prev.map(thumb =>
            thumb.pageNumber === pageNumber ? { ...thumb, isLoading: false } : thumb
          )
        );
      }
    };

    // Generate thumbnails in batches to avoid overwhelming the browser
    const batchSize = 5;
    for (let i = 0; i < pdfDocument.numPages; i += batchSize) {
      const batch = [];
      for (let j = i; j < Math.min(i + batchSize, pdfDocument.numPages); j++) {
        batch.push(generateThumbnail(j + 1));
      }
      await Promise.all(batch);
      // Small delay between batches
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    setIsGenerating(false);
  }, [pdfDocument]);

  useEffect(() => {
    if (!pdfDocument || !isVisible) {
      setThumbnails([]);
      return;
    }

    generateThumbnails();
  }, [pdfDocument, isVisible, generateThumbnails]);

  // Scroll to current page thumbnail
  useEffect(() => {
    if (thumbnailRefs.current[currentPage - 1]) {
      thumbnailRefs.current[currentPage - 1]?.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [currentPage]);

  if (!isVisible) {
    return null;
  }

  return (
    <div className={`w-64 bg-gray-50 border-r border-gray-200 overflow-y-auto ${className}`}>
      <div className="p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-4">Thumbnails</h3>

        {isGenerating && (
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            <span className="ml-2 text-sm text-gray-600">Generating...</span>
          </div>
        )}

        <div className="space-y-3">
          {thumbnails.map((thumbnail, index) => (
            <div
              key={thumbnail.pageNumber}
              ref={el => {
                thumbnailRefs.current[index] = el;
              }}
              onClick={() => onPageSelect(thumbnail.pageNumber)}
              className={`
                relative cursor-pointer rounded-lg border-2 transition-all duration-200 hover:shadow-md
                ${
                  currentPage === thumbnail.pageNumber
                    ? 'border-blue-500 shadow-lg'
                    : 'border-gray-200 hover:border-gray-300'
                }
              `}
            >
              <div className="aspect-[3/4] bg-white rounded-lg overflow-hidden">
                {thumbnail.isLoading ? (
                  <div className="w-full h-full flex items-center justify-center bg-gray-100">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                  </div>
                ) : thumbnail.canvas ? (
                  <img
                    src={thumbnail.canvas.toDataURL()}
                    alt={`Page ${thumbnail.pageNumber}`}
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gray-100 text-gray-400">
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                  </div>
                )}
              </div>

              {/* Page Number Badge */}
              <div className="absolute bottom-1 left-1 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                {thumbnail.pageNumber}
              </div>

              {/* Current Page Indicator */}
              {currentPage === thumbnail.pageNumber && (
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full"></div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
