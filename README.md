# PDF Viewer POC

Modern PDF viewer with React frontend and FastAPI backend, featuring comprehensive testing infrastructure and developer tooling.

## Prerequisites

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
# Install dependencies
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
- Form field extraction (preview)
- Enhanced metadata and validation
- Material Design UI
- Comprehensive test coverage

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

## Limitations

- No authentication
- Single user
- Ephemeral storage
- No PDF editing

## Author

Created by Dominic Fahey (domfahey@gmail.com)

## License

MIT License - See [LICENSE](LICENSE) file for details
