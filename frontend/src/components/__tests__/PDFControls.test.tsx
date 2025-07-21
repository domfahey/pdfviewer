import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PDFControls } from '../PDFViewer/PDFControls';

describe('PDFControls', () => {
  const defaultProps = {
    currentPage: 1,
    totalPages: 5,
    scale: 1.0,
    fitMode: { mode: 'width' as const },
    onPageChange: vi.fn(),
    onScaleChange: vi.fn(),
    onFitModeChange: vi.fn(),
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
    expect(screen.getByDisplayValue('1')).toBeInTheDocument();
    expect(screen.getByLabelText('Previous page')).toBeInTheDocument();
    expect(screen.getByLabelText('Next page')).toBeInTheDocument();
  });

  it('renders zoom controls', () => {
    render(<PDFControls {...defaultProps} />);

    expect(screen.getByLabelText('Zoom out')).toBeInTheDocument();
    expect(screen.getByLabelText('Zoom in')).toBeInTheDocument();
    expect(screen.getByDisplayValue('1')).toBeInTheDocument(); // Scale select
  });

  it('renders fit mode buttons', () => {
    render(<PDFControls {...defaultProps} />);

    expect(screen.getByText('Fit Width')).toBeInTheDocument();
    expect(screen.getByText('Fit Height')).toBeInTheDocument();
    expect(screen.getByText('Fit Page')).toBeInTheDocument();
  });

  it('shows advanced controls when enabled', () => {
    render(<PDFControls {...defaultProps} showAdvanced={true} />);

    expect(screen.getByLabelText('Toggle search')).toBeInTheDocument();
  });

  it('hides advanced controls when disabled', () => {
    render(<PDFControls {...defaultProps} showAdvanced={false} />);

    expect(screen.queryByLabelText('Toggle search')).not.toBeInTheDocument();
  });

  it('shows additional controls when handlers are provided', () => {
    const props = {
      ...defaultProps,
      onToggleThumbnails: vi.fn(),
      onToggleBookmarks: vi.fn(),
      onRotate: vi.fn(),
      onSearch: vi.fn(),
    };

    render(<PDFControls {...props} />);

    expect(screen.getByLabelText('Toggle thumbnails')).toBeInTheDocument();
    expect(screen.getByLabelText('Toggle bookmarks')).toBeInTheDocument();
    expect(screen.getByLabelText('Rotate 90 degrees')).toBeInTheDocument();
  });

  it('calls onPageChange when page input changes', async () => {
    const onPageChange = vi.fn();
    render(<PDFControls {...defaultProps} onPageChange={onPageChange} />);

    const pageInput = screen.getByDisplayValue('1');

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
      fireEvent.click(screen.getByLabelText('Previous page'));
    });
    expect(onPreviousPage).toHaveBeenCalled();

    await act(async () => {
      fireEvent.click(screen.getByLabelText('Next page'));
    });
    expect(onNextPage).toHaveBeenCalled();
  });

  it('disables previous button on first page', () => {
    render(<PDFControls {...defaultProps} currentPage={1} />);

    expect(screen.getByLabelText('Previous page')).toBeDisabled();
  });

  it('disables next button on last page', () => {
    render(<PDFControls {...defaultProps} currentPage={5} totalPages={5} />);

    expect(screen.getByLabelText('Next page')).toBeDisabled();
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
    render(<PDFControls {...defaultProps} onFitModeChange={onFitModeChange} />);

    await act(async () => {
      fireEvent.click(screen.getByText('Fit Width'));
    });
    expect(onFitModeChange).toHaveBeenCalledWith({ mode: 'width' });

    await act(async () => {
      fireEvent.click(screen.getByText('Fit Height'));
    });
    expect(onFitModeChange).toHaveBeenCalledWith({ mode: 'height' });

    await act(async () => {
      fireEvent.click(screen.getByText('Fit Page'));
    });
    expect(onFitModeChange).toHaveBeenCalledWith({ mode: 'page' });
  });

  it('shows search bar when search toggle is clicked', async () => {
    render(<PDFControls {...defaultProps} onSearch={vi.fn()} />);

    await act(async () => {
      fireEvent.click(screen.getByLabelText('Toggle search'));
    });

    expect(screen.getByPlaceholderText('Search in document...')).toBeInTheDocument();
  });

  it('highlights active fit mode', () => {
    render(<PDFControls {...defaultProps} fitMode={{ mode: 'height' }} />);

    const fitHeightButton = screen.getByText('Fit Height');
    expect(fitHeightButton).toHaveClass('bg-blue-500');
  });
});
