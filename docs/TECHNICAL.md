# Technical Guide

## Setup

### Prerequisites
- Python 3.11+ with UV
- Node.js 18+
- Docker (optional)
- libmagic (for file type detection)

### System Dependencies

```bash
# Install libmagic (required for PDF validation)

# macOS
brew install libmagic

# Ubuntu/Debian
sudo apt-get install libmagic1

# RHEL/CentOS/Fedora
sudo yum install file-devel

# Windows - automatically handled by python-magic-bin
```

### Install & Run

```bash
# Quick setup
make install          # Install all dependencies
make dev-backend      # Start backend
make dev-frontend     # Start frontend

# Manual setup
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]" -c configs/pyproject.toml
cd backend && uvicorn app.main:app --reload

# Docker
docker-compose up -d
```

URLs:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Development

### Quality Assurance Pipeline
```bash
# Complete QA pipeline (zero-error compliance)
make qa

# Individual commands
make lint     # Linting (ruff, eslint) - 0 errors
make format   # Formatting (ruff, black, prettier)
make type     # Type checking (mypy, tsc) - strict
make test     # Comprehensive test suite
```

**Code Quality Achievements:**
- Zero linting errors (backend + frontend)
- 100% type checking compliance
- Comprehensive test infrastructure with helper patterns
- Production-ready code standards

### Testing Infrastructure
```bash
# Test categories (optimized for performance)
make test-smoke       # Quick validation
make test-unit        # Unit tests (99% backend pass rate)
make test-integration # API integration tests
make test-e2e        # End-to-end workflow tests
make test-coverage   # Coverage reports (80% threshold)

# Advanced testing features
make test-watch      # Watch mode for development
make test-debug      # Debug mode with breakpoints
make test-parallel   # Parallel execution for speed
make test-specific TEST=path/to/test  # Run specific tests
```

**Test Infrastructure Improvements:**
- Helper functions reduce code duplication by 30-40%
- Standardized mock patterns with builder classes (`PDFServiceMockBuilder`, `MockResponseBuilder`)
- Fixture factories for consistent test data generation
- Context managers for proper mock lifecycle
- Performance optimizations prevent flaky tests
- Comprehensive assertion helpers for common patterns

### Type Safety & Code Quality
- **Python 3.11+** with modern type annotations
  - Union types using `X | Y` syntax
  - Direct `datetime.UTC` usage
  - Modern `isinstance(x, int | float)` patterns
  - Zero mypy errors across 18 source files
- **TypeScript** strict compliance
  - Zero ESLint errors (fixed all 34 @typescript-eslint/no-explicit-any)
  - Proper type assertions using `unknown` casting
  - Comprehensive interface definitions
- **Runtime Validation**
  - Pydantic v2 models with computed fields
  - FastAPI automatic validation
  - React 19.1 with strict mode compatibility

## Project Structure

```
.
├── Makefile              # Development commands
├── backend/
│   ├── app/
│   │   ├── api/         # FastAPI endpoints
│   │   ├── models/      # Pydantic v2 models
│   │   ├── services/    # Business logic
│   │   ├── middleware/  # CORS, logging
│   │   └── utils/       # Helpers, decorators
│   └── uploads/         # Temporary PDF storage
├── frontend/
│   ├── src/
│   │   ├── components/  # React 19 components
│   │   ├── hooks/       # Custom React hooks
│   │   ├── services/    # API client
│   │   └── types/       # TypeScript types
│   └── coverage/        # Test coverage reports
├── tests/
│   ├── test_*.py        # Unit tests
│   ├── integration/     # API integration tests
│   │   ├── api/         # Endpoint tests
│   │   └── fixtures/    # Test PDFs
│   ├── e2e/            # Playwright E2E tests
│   └── README.md       # Test documentation
└── docs/               # Project documentation
```

## Environment Variables

```env
# Backend
LOG_LEVEL=DEBUG
JSON_LOGS=false
MAX_FILE_SIZE=52428800  # 50MB

# Frontend  
VITE_API_BASE_URL=http://localhost:8000/api
```

## Logging

- Structured logging with correlation IDs
- API decorators: `@log_api_call`, `@log_file_operation`
- Debug mode enabled by default

## Docker Commands

```bash
docker-compose logs -f   # View logs
docker-compose down      # Stop
docker-compose build     # Rebuild
```

## Key Features

- Full-text PDF search with highlighting
- URL and local file loading
- Test PDF loader for demos
- Form field extraction with ground truth comparison (preview)
- Virtual scrolling for performance
- Material Design UI components (MUI v7)
- Comprehensive test coverage

## Test Infrastructure

- **Unit Tests**: Component and function isolation (99% backend pass rate)
- **Integration Tests**: API endpoint validation with local mocks
- **E2E Tests**: User workflow verification with Playwright
- **Performance Tests**: Load testing and response optimization
- **Coverage**: 80% threshold with detailed reporting
- **Helper Patterns**: 30-40% code reduction through reusable test utilities

**Key Test Files:**
- `tests/helpers/test_assertions.py`: Reusable assertion patterns
- `tests/helpers/mock_helpers.py`: Standardized mock builders
- `tests/config.py`: Centralized test configuration

See [Test Guide](../tests/README.md) for details.

## Security Practices

- **Secret Detection**: Pre-commit hooks prevent accidental commits
- **Environment Variables**: All configuration via `.env` files
- **Git History**: Cleaned of all uploaded files and caches
- **Log Sanitization**: Automatic redaction of sensitive data
- **File Validation**: Path traversal protection

## Production Notes

- Enable JSON logs: `JSON_LOGS=true`
- Configure CORS for production domains
- Set up persistent storage for uploads
- Review security configuration in CONTRIBUTING.md