# PDF Viewer POC

Modern PDF viewer with React 19.1 frontend and FastAPI backend, featuring comprehensive testing infrastructure, ground truth comparison UI, and developer tooling.

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
make lint     # Run linters (ruff, eslint)
make format   # Format code (ruff, black, prettier)
make type     # Type check (mypy, tsc)
make test     # Run test suite
make qa       # Full quality checks
```

See all commands: `make help`

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
- Comprehensive test coverage
- Modern Python 3.11+ type annotations
- React 19.1 with TypeScript

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
# Quick smoke tests
make test-smoke

# Full test suite
make test-all

# Specific test categories
make test-unit        # Unit tests
make test-integration # Integration tests
make test-e2e        # End-to-end tests

# With coverage
make test-coverage
```

See [Test Documentation](tests/README.md) for details.

## Project Structure

```
pdfviewer/
├── configs/           # Configuration files
│   ├── Makefile      # Development commands
│   ├── pyproject.toml # Python project config
│   └── playwright.config.ts # E2E test config
├── docs/             # Documentation
├── scripts/          # Build and utility scripts
├── logs/             # Application logs (gitignored)
├── artifacts/        # Build artifacts, coverage reports
├── backend/          # Python FastAPI backend
├── frontend/         # React frontend
├── tests/            # Test suites (unit, integration, e2e)
├── README.md         # This file
├── CHANGELOG.md      # Version history
├── CLAUDE.md         # AI assistant instructions
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
- [Performance Optimization](docs/PERFORMANCE.md)
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
