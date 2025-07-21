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
uv pip install -e ".[dev]"
cd backend && uvicorn app.main:app --reload

# Docker
docker-compose up -d
```

URLs:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Development

### Quality Assurance
```bash
# All checks at once
make qa

# Individual commands
make lint     # Linting (ruff, eslint)
make format   # Formatting (black, prettier)
make type     # Type checking (mypy, tsc)
make test     # Run tests
```

### Testing
```bash
# Test categories
make test-smoke       # Quick validation
make test-unit        # Unit tests only
make test-integration # API integration tests
make test-e2e        # End-to-end tests
make test-coverage   # With coverage reports

# Advanced testing
make test-watch      # Watch mode
make test-debug      # Debug mode
make test-parallel   # Parallel execution
```

### Type Safety
- Python 3.11+ with modern type annotations
- Strict typing for business logic
- Relaxed typing for tests and utilities
- Pydantic v2 for runtime validation

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

- **Unit Tests**: Component and function isolation
- **Integration Tests**: API endpoint validation
- **E2E Tests**: User workflow verification
- **Performance Tests**: Load and response times
- **Coverage**: 80% threshold (configurable)

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