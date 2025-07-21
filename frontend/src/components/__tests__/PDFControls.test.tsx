import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PDFControls } from '../PDFViewer/PDFControls';

describe('PDFControls', () => {
  const defaultProps = {
    currentPage: 1,
    totalPages: 5,
    scale: 1.0,
    fitMode: { mode: 'width' as const },
    viewMode: 'original' as const,
    onPageChange: vi.fn(),
    onScaleChange: vi.fn(),
    onFitModeChange: vi.fn(),
    onViewModeChange: vi.fn(),
    onPreviousPage: vi.fn(),
    onNextPage: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders basic navigation controls', () => {
    render(<PDFControls {...defaultProps} />);

    expect(screen.getByText('Page')).toBeInTheDocument();
    expect(screen.getByText('of 5')).toBeInTheDocument();
    expect(screen.getByRole('spinbutton')).toBeInTheDocument();
    expect(screen.getByLabelText('Previous page')).toBeInTheDocument();
    expect(screen.getByLabelText('Next page')).toBeInTheDocument();
  });

  it('renders zoom controls', () => {
    render(<PDFControls {...defaultProps} />);

    expect(screen.getByLabelText('Zoom out')).toBeInTheDocument();
    expect(screen.getByLabelText('Zoom in')).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toBeInTheDocument(); // Scale select
  });

  it('renders fit mode buttons', () => {
    render(<PDFControls {...defaultProps} />);

    expect(screen.getByLabelText('fit width')).toBeInTheDocument();
    expect(screen.getByLabelText('fit height')).toBeInTheDocument();
    expect(screen.getByLabelText('fit page')).toBeInTheDocument();
  });

  it('shows advanced controls when enabled', () => {
    render(<PDFControls {...defaultProps} showAdvanced={true} />);

    expect(screen.getByLabelText('Search in document')).toBeInTheDocument();
  });

  it('hides advanced controls when disabled', () => {
    render(<PDFControls {...defaultProps} showAdvanced={false} />);

    expect(screen.queryByLabelText('Search in document')).not.toBeInTheDocument();
  });

  it('shows additional controls when handlers are provided', () => {
    const props = {
      ...defaultProps,
      onToggleThumbnails: vi.fn(),
      onToggleBookmarks: vi.fn(),
      onToggleExtractedFields: vi.fn(),
      onRotate: vi.fn(),
      onSearch: vi.fn(),
    };

    render(<PDFControls {...props} />);

    expect(screen.getByLabelText('Toggle thumbnails')).toBeInTheDocument();
    expect(screen.getByLabelText('Document info')).toBeInTheDocument();
    expect(screen.getByLabelText('Extracted fields')).toBeInTheDocument();
    expect(screen.getByLabelText('Rotate 90 degrees')).toBeInTheDocument();
  });

  it('calls onPageChange when page input changes', async () => {
    const onPageChange = vi.fn();
    render(<PDFControls {...defaultProps} onPageChange={onPageChange} />);

    const pageInput = screen.getByRole('spinbutton');

    await act(async () => {
      fireEvent.change(pageInput, { target: { value: '3' } });
    });

    expect(onPageChange).toHaveBeenCalledWith(3);
  });

  it('calls navigation handlers when buttons are clicked', async () => {
    const onPreviousPage = vi.fn();
    const onNextPage = vi.fn();

    render(
      <PDFControls
        {...defaultProps}
        currentPage={2}
        onPreviousPage={onPreviousPage}
        onNextPage={onNextPage}
      />
    );

    await act(async () => {
      const prevButton = screen.getByLabelText('Previous page').querySelector('button');
      fireEvent.click(prevButton!);
    });
    expect(onPreviousPage).toHaveBeenCalled();

    await act(async () => {
      const nextButton = screen.getByLabelText('Next page').querySelector('button');
      fireEvent.click(nextButton!);
    });
    expect(onNextPage).toHaveBeenCalled();
  });

  it('disables previous button on first page', () => {
    render(<PDFControls {...defaultProps} currentPage={1} />);

    const prevButton = screen.getByLabelText('Previous page').querySelector('button');
    expect(prevButton).toBeDisabled();
  });

  it('disables next button on last page', () => {
    render(<PDFControls {...defaultProps} currentPage={5} totalPages={5} />);

    const nextButton = screen.getByLabelText('Next page').querySelector('button');
    expect(nextButton).toBeDisabled();
  });

  it('calls onScaleChange when zoom controls are used', async () => {
    const onScaleChange = vi.fn();
    render(<PDFControls {...defaultProps} onScaleChange={onScaleChange} />);

    await act(async () => {
      fireEvent.click(screen.getByLabelText('Zoom in'));
    });
    expect(onScaleChange).toHaveBeenCalledWith(1.25);

    await act(async () => {
      fireEvent.click(screen.getByLabelText('Zoom out'));
    });
    expect(onScaleChange).toHaveBeenCalledWith(0.75);
  });

  it('calls onFitModeChange when fit buttons are clicked', async () => {
    const onFitModeChange = vi.fn();
    render(
      <PDFControls
        {...defaultProps}
        fitMode={{ mode: 'custom' }}
        onFitModeChange={onFitModeChange}
      />
    );

    const fitButtons = screen.getAllByRole('button');
    const heightButton = fitButtons.find(button => button.getAttribute('value') === 'height');
    const pageButton = fitButtons.find(button => button.getAttribute('value') === 'page');

    await act(async () => {
      fireEvent.click(heightButton!);
    });
    expect(onFitModeChange).toHaveBeenCalledWith({ mode: 'height' });

    await act(async () => {
      fireEvent.click(pageButton!);
    });
    expect(onFitModeChange).toHaveBeenCalledWith({ mode: 'page' });
  });

  it('shows search bar when search toggle is clicked', async () => {
    render(<PDFControls {...defaultProps} onSearch={vi.fn()} />);

    await act(async () => {
      fireEvent.click(screen.getByLabelText('Search in document'));
    });

    expect(screen.getByPlaceholderText('Search in document...')).toBeInTheDocument();
  });

  it('renders view mode toggle', () => {
    render(<PDFControls {...defaultProps} />);

    expect(screen.getByLabelText('original pdf view')).toBeInTheDocument();
    expect(screen.getByLabelText('digital markdown view')).toBeInTheDocument();
    expect(screen.getByText('Original')).toBeInTheDocument();
    expect(screen.getByText('Digital')).toBeInTheDocument();
  });

  it('calls onViewModeChange when view mode buttons are clicked', async () => {
    const onViewModeChange = vi.fn();
    render(<PDFControls {...defaultProps} onViewModeChange={onViewModeChange} />);

    await act(async () => {
      fireEvent.click(screen.getByLabelText('digital markdown view'));
    });
    expect(onViewModeChange).toHaveBeenCalledWith('digital');
  });
});
