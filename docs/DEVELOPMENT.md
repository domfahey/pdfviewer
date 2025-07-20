# Development Guide

This guide covers everything you need to know for developing and contributing to the PDF Viewer project.

## Development Environment Setup

### Prerequisites

- **Python 3.9+** with UV package manager
- **Node.js 18+** with npm
- **Git** for version control
- **VS Code** (recommended) with extensions

### Required VS Code Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "ms-python.mypy-type-checker",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-typescript-next"
  ]
}
```

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-org/pdf-viewer.git
cd pdf-viewer

# Backend setup
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Frontend setup
cd frontend
npm install
cd ..

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

### Environment Configuration

Create environment files for development:

**.env (Backend)**:
```bash
LOG_LEVEL=DEBUG
JSON_LOGS=false
ENVIRONMENT=development
MAX_FILE_SIZE=52428800
UPLOAD_DIR=uploads
```

**frontend/.env.local**:
```bash
VITE_API_BASE_URL=http://localhost:8000/api
VITE_NODE_ENV=development
```

## Development Workflow

### Starting the Development Environment

```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev

# Terminal 3: Run tests in watch mode (optional)
pytest --watch
```

### Development URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## Code Organization

### Backend Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── core/                # Core configuration
│   │   ├── __init__.py
│   │   └── logging.py       # Logging configuration
│   ├── middleware/          # HTTP middleware
│   │   ├── __init__.py
│   │   └── logging.py       # Request correlation middleware
│   ├── utils/               # Utility functions
│   │   ├── __init__.py
│   │   └── logger.py        # Logging utilities
│   ├── api/                 # API routes
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoints
│   │   ├── upload.py        # File upload endpoints
│   │   └── pdf.py           # PDF management endpoints
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   └── pdf.py           # PDF-related Pydantic models
│   └── services/            # Business logic
│       ├── __init__.py
│       └── pdf_service.py   # PDF processing service
└── pyproject.toml           # Dependencies and tool configuration
```

### Frontend Structure

```
frontend/src/
├── components/              # React components
│   ├── PDFViewer/          # PDF viewer components
│   │   ├── PDFViewer.tsx
│   │   ├── VirtualPDFViewer.tsx
│   │   ├── PDFPage.tsx
│   │   ├── PDFControls.tsx
│   │   ├── PDFThumbnails.tsx
│   │   └── PDFMetadataPanel.tsx
│   ├── Upload/             # File upload components
│   │   └── FileUpload.tsx
│   ├── Navigation/         # Navigation components
│   └── UI/                 # Reusable UI components
├── hooks/                  # Custom React hooks
│   ├── usePDFDocument.ts
│   └── useFileUpload.ts
├── services/               # API service layer
│   ├── api.ts
│   └── pdfService.ts
├── types/                  # TypeScript type definitions
│   ├── pdf.types.ts
│   └── annotation.types.ts
├── utils/                  # Utility functions
├── styles/                 # Global styles
└── test/                   # Test utilities
    └── setup.ts
```

## Development Standards

### Python Code Standards

#### Code Style
- **PEP 8** compliance enforced by ruff
- **Black** for code formatting
- **Type hints** required for all functions
- **Docstrings** for all public functions and classes

#### Example Function
```python
from typing import Optional
from pathlib import Path
from backend.app.core.logging import get_logger

logger = get_logger(__name__)

async def process_pdf_file(
    file_path: Path,
    extract_metadata: bool = True,
    validate_content: bool = True
) -> Optional[PDFMetadata]:
    """
    Process a PDF file and extract metadata.
    
    Args:
        file_path: Path to the PDF file
        extract_metadata: Whether to extract document metadata
        validate_content: Whether to validate PDF structure
        
    Returns:
        PDFMetadata object if successful, None otherwise
        
    Raises:
        PDFProcessingError: If file processing fails
        FileNotFoundError: If file doesn't exist
    """
    logger.info("Processing PDF file", file_path=str(file_path))
    
    try:
        # Implementation here
        with PerformanceTracker("PDF processing", logger):
            # Processing logic
            pass
            
    except Exception as e:
        logger.error("PDF processing failed", error=str(e))
        raise PDFProcessingError(f"Failed to process {file_path}") from e
```

#### Error Handling
```python
from backend.app.utils.logger import log_exception_context

try:
    result = await risky_operation()
except SpecificException as e:
    # Handle specific exceptions
    logger.warning("Expected error occurred", error=str(e))
    return fallback_result()
except Exception as e:
    # Log unexpected exceptions with context
    log_exception_context(
        logger,
        "risky operation",
        e,
        operation_id="op123",
        user_context="additional_info"
    )
    raise
```

### TypeScript Code Standards

#### Component Structure
```typescript
import React, { useState, useCallback, useEffect } from 'react';
import { PDFDocument } from '../types/pdf.types';
import { usePDFDocument } from '../hooks/usePDFDocument';

interface PDFViewerProps {
  fileId: string;
  onError?: (error: string) => void;
  onPageChange?: (page: number) => void;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({
  fileId,
  onError,
  onPageChange
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const { document, loading, error } = usePDFDocument(fileId);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
    onPageChange?.(page);
  }, [onPageChange]);

  useEffect(() => {
    if (error) {
      onError?.(error);
    }
  }, [error, onError]);

  if (loading) {
    return <div className="flex justify-center p-4">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-500 p-4">Error: {error}</div>;
  }

  return (
    <div className="pdf-viewer">
      {/* Component JSX */}
    </div>
  );
};
```

#### Custom Hooks
```typescript
import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import { PDFMetadata } from '../types/pdf.types';

interface UsePDFDocumentReturn {
  document: PDFMetadata | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const usePDFDocument = (fileId: string): UsePDFDocumentReturn => {
  const [document, setDocument] = useState<PDFMetadata | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocument = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const metadata = await apiService.getMetadata(fileId);
      setDocument(metadata);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  useEffect(() => {
    if (fileId) {
      fetchDocument();
    }
  }, [fileId, fetchDocument]);

  return {
    document,
    loading,
    error,
    refetch: fetchDocument
  };
};
```

### Testing Standards

#### Backend Testing
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from backend.app.main import app
from backend.app.services.pdf_service import PDFService

client = TestClient(app)

class TestPDFUpload:
    """Test suite for PDF upload functionality."""
    
    def test_upload_valid_pdf(self, sample_pdf_file):
        """Test uploading a valid PDF file."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data
        assert data["filename"] == "test.pdf"
        assert data["mime_type"] == "application/pdf"
    
    def test_upload_invalid_file_type(self):
        """Test uploading an invalid file type."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", b"invalid content", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Only PDF files are allowed" in response.json()["detail"]
    
    @patch('backend.app.services.pdf_service.magic.from_file')
    def test_upload_with_mocked_validation(self, mock_magic):
        """Test upload with mocked MIME type validation."""
        mock_magic.return_value = "application/pdf"
        
        with patch.object(PDFService, '_extract_pdf_metadata') as mock_extract:
            mock_extract.return_value = Mock(page_count=1, file_size=1024)
            
            response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", b"pdf content", "application/pdf")}
            )
            
            assert response.status_code == 200
            mock_extract.assert_called_once()
```

#### Frontend Testing
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FileUpload } from '../FileUpload';
import { useFileUpload } from '../../hooks/useFileUpload';

// Mock the hook
vi.mock('../../hooks/useFileUpload');
const mockUseFileUpload = vi.mocked(useFileUpload);

describe('FileUpload', () => {
  const mockOnUploadSuccess = vi.fn();
  const mockUploadFile = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseFileUpload.mockReturnValue({
      uploading: false,
      uploadProgress: 0,
      error: null,
      uploadFile: mockUploadFile,
      clearError: vi.fn(),
    });
  });

  it('renders upload interface', () => {
    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);
    
    expect(screen.getByText(/drag.*drop.*pdf/i)).toBeInTheDocument();
    expect(screen.getByText(/click to browse/i)).toBeInTheDocument();
  });

  it('handles file selection and upload', async () => {
    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);
    
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const input = screen.getByRole('button').querySelector('input[type="file"]');
    
    fireEvent.change(input!, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(mockUploadFile).toHaveBeenCalledWith(file);
    });
  });

  it('shows error state', () => {
    mockUseFileUpload.mockReturnValue({
      uploading: false,
      uploadProgress: 0,
      error: 'Upload failed',
      uploadFile: mockUploadFile,
      clearError: vi.fn(),
    });

    render(<FileUpload onUploadSuccess={mockOnUploadSuccess} />);
    
    expect(screen.getByText('Upload Error')).toBeInTheDocument();
    expect(screen.getByText('Upload failed')).toBeInTheDocument();
  });
});
```

## Debugging

### Backend Debugging

#### VS Code Launch Configuration
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/.venv/bin/uvicorn",
      "args": [
        "backend.app.main:app",
        "--reload",
        "--port",
        "8000"
      ],
      "env": {
        "LOG_LEVEL": "DEBUG",
        "JSON_LOGS": "false"
      },
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

#### Logging for Debugging
```python
from backend.app.core.logging import get_logger

logger = get_logger(__name__)

# Debug logging with context
logger.debug("Processing request", 
             request_id="123",
             user_id="user456",
             file_size=1024)

# Performance debugging
with PerformanceTracker("slow_operation", logger, min_duration_ms=100):
    # Only logs if operation takes more than 100ms
    slow_operation()
```

### Frontend Debugging

#### React DevTools
- Install React DevTools browser extension
- Use component tree to inspect state and props
- Profile component performance

#### Browser DevTools
```typescript
// Add debug logging
console.group('PDF Viewer Debug');
console.log('Current page:', currentPage);
console.log('Document loaded:', !!document);
console.log('PDF.js version:', pdfjsLib.version);
console.groupEnd();

// Performance debugging
console.time('PDF Render');
await renderPDFPage(pageNumber);
console.timeEnd('PDF Render');
```

#### Error Boundaries
```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error boundary caught an error:', error, errorInfo);
    
    // Log to monitoring service
    if (process.env.NODE_ENV === 'production') {
      // Send to Sentry or other error tracking
    }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <details>
            {this.state.error?.message}
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}
```

## Performance Optimization

### Backend Performance

#### Database Optimization
```python
# Use async database operations
from databases import Database

database = Database("postgresql://user:password@host/db")

async def get_pdf_metadata(file_id: str) -> Optional[PDFMetadata]:
    query = "SELECT * FROM pdf_files WHERE id = :file_id"
    result = await database.fetch_one(query, {"file_id": file_id})
    return PDFMetadata(**result) if result else None
```

#### Caching
```python
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@lru_cache(maxsize=128)
def get_pdf_metadata_cached(file_id: str) -> PDFMetadata:
    """Cache PDF metadata in memory."""
    return get_pdf_metadata(file_id)

async def get_pdf_metadata_redis(file_id: str) -> Optional[PDFMetadata]:
    """Cache PDF metadata in Redis."""
    cache_key = f"pdf_metadata:{file_id}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return PDFMetadata.parse_raw(cached)
    
    metadata = await get_pdf_metadata(file_id)
    if metadata:
        redis_client.setex(cache_key, 3600, metadata.json())
    
    return metadata
```

### Frontend Performance

#### React Optimization
```typescript
import React, { memo, useMemo, useCallback } from 'react';

// Memoize expensive components
export const PDFPage = memo<PDFPageProps>(({ pageNumber, scale, document }) => {
  const renderedPage = useMemo(() => {
    if (!document) return null;
    return renderPDFPage(document, pageNumber, scale);
  }, [document, pageNumber, scale]);

  return <div className="pdf-page">{renderedPage}</div>;
});

// Memoize expensive calculations
const PDFViewer: React.FC<PDFViewerProps> = ({ document }) => {
  const visiblePages = useMemo(() => {
    return calculateVisiblePages(scrollTop, containerHeight, pageHeight);
  }, [scrollTop, containerHeight, pageHeight]);

  const handleScroll = useCallback((event: React.UIEvent) => {
    setScrollTop(event.currentTarget.scrollTop);
  }, []);

  return (
    <div onScroll={handleScroll}>
      {visiblePages.map(pageNum => (
        <PDFPage key={pageNum} pageNumber={pageNum} />
      ))}
    </div>
  );
};
```

#### Virtual Scrolling
```typescript
import { FixedSizeList } from 'react-window';

const VirtualPDFViewer: React.FC<VirtualPDFViewerProps> = ({ 
  document, 
  pageHeight = 800 
}) => {
  const renderPage = useCallback(({ index, style }: ListChildComponentProps) => {
    return (
      <div style={style}>
        <PDFPage pageNumber={index + 1} document={document} />
      </div>
    );
  }, [document]);

  return (
    <FixedSizeList
      height={600}
      itemCount={document.page_count}
      itemSize={pageHeight}
      width="100%"
    >
      {renderPage}
    </FixedSizeList>
  );
};
```

## Git Workflow

### Branch Naming Convention
- `feature/feature-name` - New features
- `bugfix/bug-description` - Bug fixes
- `hotfix/critical-fix` - Critical production fixes
- `refactor/component-name` - Code refactoring
- `docs/section-name` - Documentation updates

### Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(pdf-viewer): add zoom controls with keyboard shortcuts

- Add zoom in/out buttons
- Implement keyboard shortcuts (Ctrl+/Ctrl-)
- Add fit-to-page and fit-to-width options

Closes #123
```

### Pre-commit Hooks

`.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black

  - repo: local
    hooks:
      - id: frontend-lint
        name: Frontend Lint
        entry: npm run lint
        language: system
        files: ^frontend/
        pass_filenames: false

      - id: frontend-type-check
        name: Frontend Type Check
        entry: npm run type-check
        language: system
        files: ^frontend/
        pass_filenames: false
```

## Continuous Integration

### GitHub Actions

`.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.11]

    steps:
    - uses: actions/checkout@v4
    
    - name: Install UV
      uses: astral-sh/setup-uv@v1
      with:
        version: "latest"
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: uv pip install -e ".[dev]"
    
    - name: Run linting
      run: |
        ruff check .
        black --check .
        mypy . --ignore-missing-imports
    
    - name: Run tests
      run: pytest --cov=backend/app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: 18
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run linting
      run: |
        cd frontend
        npm run lint
        npm run type-check
    
    - name: Run tests
      run: |
        cd frontend
        npm run test:coverage
    
    - name: Build
      run: |
        cd frontend
        npm run build

  integration-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Build and test with Docker Compose
      run: |
        docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
        docker-compose -f docker-compose.test.yml down
```

## IDE Configuration

### VS Code Settings

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  
  "typescript.preferences.organizeImports": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true,
    "source.fixAll.eslint": true
  },
  
  "tailwindCSS.includeLanguages": {
    "typescript": "typescript",
    "typescriptreact": "typescriptreact"
  },
  
  "files.associations": {
    "*.css": "tailwindcss"
  }
}
```

### VS Code Tasks

`.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Backend Dev Server",
      "type": "shell",
      "command": "uvicorn",
      "args": ["backend.app.main:app", "--reload", "--port", "8000"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "new"
      },
      "problemMatcher": []
    },
    {
      "label": "Start Frontend Dev Server",
      "type": "shell",
      "command": "npm",
      "args": ["run", "dev"],
      "options": {
        "cwd": "${workspaceFolder}/frontend"
      },
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "new"
      },
      "problemMatcher": []
    },
    {
      "label": "Run All Tests",
      "type": "shell",
      "command": "./check-all.sh",
      "group": "test",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "new"
      },
      "problemMatcher": []
    }
  ]
}
```

This development guide provides comprehensive information for setting up, developing, and contributing to the PDF Viewer project. Follow these standards and practices to maintain code quality and consistency across the project.