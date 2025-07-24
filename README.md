# PDF Viewer POC

Modern PDF viewer POC with React 19.1 frontend and FastAPI backend. Features comprehensive testing infrastructure, zero-error code quality, and advanced developer tooling.

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher

### System Dependencies

The backend requires `libmagic` for file type detection:

```bash
# macOS
brew install libmagic

# Ubuntu/Debian
sudo apt-get install libmagic1

# RHEL/CentOS/Fedora
sudo yum install file-devel
# or
sudo dnf install file-devel

# Windows
# python-magic-bin will be installed automatically
```

## Quick Start

```bash
# Optional: Install uv for faster Python dependency management
make setup-uv

# Install dependencies (automatically uses uv if available, falls back to pip)
make install

# Run development servers
make dev-backend   # Backend on http://localhost:8000
make dev-frontend  # Frontend on http://localhost:5173

# Or use Docker
docker-compose up -d
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Development Commands

```bash
make lint     # Run linters (ruff, eslint) - passes with zero errors
make format   # Format code (ruff, black, prettier) 
make type     # Type check (mypy, tsc) - strict compliance
make test     # Run comprehensive test suite
make qa       # Full quality pipeline (lint, format, type, test)
```

See all 40+ commands: `make help`

## Features

- PDF rendering with virtual scrolling
- Full-text search with highlighting
- Load PDFs from URLs or local files
- Test PDF loader for quick demos
- Form field extraction with ground truth comparison UI
  - Toggle between extraction-only and comparison views
  - Accuracy metrics (exact, similar, different matches)
  - Visual indicators for match quality
- Enhanced metadata and validation
- Material Design UI (MUI v7)
- Comprehensive test coverage with helper patterns
- Modern Python 3.11+ type annotations
- React 19.1 with strict TypeScript compliance
- Zero linting errors with ESLint and Ruff
- Production-ready code quality

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/upload` | Upload PDF (50MB limit) |
| `POST /api/load-url` | Load PDF from URL |
| `GET /api/pdf/{id}` | Download PDF |
| `GET /api/metadata/{id}` | Get metadata |
| `DELETE /api/pdf/{id}` | Delete PDF |

See [API Documentation](docs/API.md) for details.

## Testing

```bash
# Quick smoke tests (health checks)
make test-smoke

# Full test suite (99% backend pass rate)
make test-all

# Specific test categories
make test-unit        # Unit tests with helper patterns
make test-integration # API integration tests
make test-e2e        # End-to-end workflow tests

# Advanced testing
make test-coverage    # Coverage reports
make test-debug      # Debug failing tests
make test-parallel   # Parallel execution
```

**Test Infrastructure Features:**
- Helper functions reduce code duplication by 30-40%
- Standardized mock patterns with builder classes
- Fixture factories for consistent test data
- Performance optimizations prevent flaky tests
- Comprehensive assertion helpers

See [Test Documentation](tests/README.md) for details.

## Project Structure

```
pdfviewer/
├── configs/           # Configuration files (Makefile, pyproject.toml)
├── docs/             # Comprehensive documentation
├── scripts/          # Build and utility scripts
├── logs/             # Application logs (gitignored)
├── artifacts/        # Build artifacts, coverage reports
├── backend/          # Python FastAPI backend
├── frontend/         # React 19.1 TypeScript frontend
├── tests/            # Comprehensive test suites
│   ├── helpers/      # Reusable test utilities (reduce duplication 30-40%)
│   ├── unit/         # Unit tests (99% backend pass rate)
│   ├── integration/  # API integration tests
│   └── e2e/          # End-to-end workflow tests
├── README.md         # This file (comprehensive guide)
├── CHANGELOG.md      # Version history with detailed improvements
├── CLAUDE.md         # AI assistant instructions (zero-error standards)
└── package.json      # Root package management
```

## Security

```bash
# Install pre-commit hooks
pre-commit install

# Run security scan
detect-secrets scan

# Scan for secrets in git history
gitleaks detect
```

This project implements:
- Pre-commit hooks for secret detection
- Environment variables for all configuration
- Automatic log sanitization for sensitive data
- No hardcoded credentials or API keys
- Git history cleaned of uploaded files
- Comprehensive `.gitignore` patterns

⚠️ **Note**: Git history was rewritten on 2025-01-21 to remove sensitive files. 
Collaborators should re-clone the repository.

## Documentation

- [API Reference](docs/API.md)
- [Technical Guide](docs/TECHNICAL.md)
- [Test Guide](tests/README.md)
- [Technical Debt](docs/TECHNICAL_DEBT.md)

## Limitations

- No authentication
- Single user
- Ephemeral storage
- No PDF editing

## Author

Created by Dominic Fahey (domfahey@gmail.com)

## License

MIT License - See [LICENSE](LICENSE) file for details
