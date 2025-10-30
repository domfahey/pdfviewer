import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Card,
  CardMedia,
  Badge,
  Skeleton,
} from '@mui/material';
import { renderPageToCanvas } from '../../utils/canvasRenderer';

interface PDFThumbnailsProps {
  pdfDocument: pdfjsLib.PDFDocumentProxy | null;
  currentPage: number;
  onPageSelect: (page: number) => void;
  isVisible: boolean;
  width: number;
  onResize: (width: number) => void;
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
  width,
  onResize,
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
        
        // Use shared canvas rendering utility with thumbnail scale
        const canvas = await renderPageToCanvas(page, { scale: 0.2, createNew: true });

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

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = width;

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - startX;
      const newWidth = Math.min(Math.max(200, startWidth + deltaX), 500);
      onResize(newWidth);
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  if (!isVisible) {
    return null;
  }

  return (
    <Box
      sx={{
        width: `${width}px`,
        height: '100%',
        display: 'flex',
        flexDirection: 'row',
        position: 'relative',
      }}
      className={className}
    >
      {/* Panel Content */}
      <Paper
        elevation={1}
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          bgcolor: 'background.paper',
          borderRadius: 0,
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 2,
            borderBottom: '1px solid',
            borderColor: 'divider',
            bgcolor: 'grey.50',
          }}
        >
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            Thumbnails
          </Typography>
        </Box>

        {/* Content */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
          {isGenerating && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                py: 4,
                gap: 2,
              }}
            >
              <CircularProgress size={24} />
              <Typography variant="body2" color="text.secondary">
                Generating thumbnails...
              </Typography>
            </Box>
          )}

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {thumbnails.map((thumbnail, index) => (
              <Card
                key={thumbnail.pageNumber}
                ref={el => {
                  thumbnailRefs.current[index] = el;
                }}
                onClick={() => onPageSelect(thumbnail.pageNumber)}
                sx={{
                  cursor: 'pointer',
                  transition: 'all 0.2s ease-in-out',
                  border: '2px solid',
                  borderColor:
                    currentPage === thumbnail.pageNumber ? 'primary.main' : 'transparent',
                  '&:hover': {
                    elevation: 4,
                    borderColor: currentPage === thumbnail.pageNumber ? 'primary.main' : 'grey.300',
                    transform: 'translateY(-1px)',
                  },
                  position: 'relative',
                }}
                elevation={currentPage === thumbnail.pageNumber ? 3 : 1}
              >
                <Box sx={{ aspectRatio: '3/4', position: 'relative' }}>
                  {thumbnail.isLoading ? (
                    <Box
                      sx={{
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        bgcolor: 'grey.100',
                      }}
                    >
                      <CircularProgress size={20} />
                    </Box>
                  ) : thumbnail.canvas ? (
                    <CardMedia
                      component="img"
                      image={thumbnail.canvas.toDataURL()}
                      alt={`Page ${thumbnail.pageNumber}`}
                      sx={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'contain',
                        bgcolor: 'white',
                      }}
                    />
                  ) : (
                    <Skeleton
                      variant="rectangular"
                      width="100%"
                      height="100%"
                      sx={{ bgcolor: 'grey.200' }}
                    />
                  )}

                  {/* Page Number Badge */}
                  <Badge
                    badgeContent={thumbnail.pageNumber}
                    color={currentPage === thumbnail.pageNumber ? 'primary' : 'default'}
                    sx={{
                      position: 'absolute',
                      bottom: 8,
                      left: 8,
                      '& .MuiBadge-badge': {
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        minWidth: 24,
                        height: 24,
                      },
                    }}
                  >
                    <Box />
                  </Badge>

                  {/* Current Page Indicator */}
                  {currentPage === thumbnail.pageNumber && (
                    <Box
                      sx={{
                        position: 'absolute',
                        top: -4,
                        right: -4,
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        bgcolor: 'primary.main',
                        border: '2px solid white',
                      }}
                    />
                  )}
                </Box>
              </Card>
            ))}
          </Box>
        </Box>
      </Paper>

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
    </Box>
  );
};
