# PDF Viewer POC

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React Version](https://img.shields.io/badge/react-19.1-blue.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-black.svg)](https://github.com/psf/black)
[![TypeScript](https://img.shields.io/badge/typescript-5.6-blue.svg)](https://www.typescriptlang.org/)

Modern PDF viewer with React 19.1 frontend and FastAPI backend, featuring comprehensive testing infrastructure, ground truth comparison UI, and developer tooling.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Commands](#development-commands)
- [Features](#features)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Security](#security)
- [Documentation](#documentation)
- [Limitations](#limitations)
- [Author](#author)
- [License](#license)

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

**Three ways to get started:**

### 1. Using Make (Recommended)
```bash
# Install dependencies (automatically uses uv if available, falls back to pip)
make install

# Run development servers (in separate terminals)
make dev-backend   # Backend on http://localhost:8000
make dev-frontend  # Frontend on http://localhost:5173
```

### 2. Using Docker
```bash
docker-compose up -d
```

### 3. Manual Setup
```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Frontend (in new terminal)
cd frontend
npm install
npm run dev
```

**Access the application:**
- 🌐 Frontend: http://localhost:5173
- 🔧 Backend: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs

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

### Core Functionality
- ✅ **PDF Rendering** with virtual scrolling for optimal performance
- 🔍 **Full-text Search** with highlighting and navigation
- 📥 **Flexible Loading** from URLs or local file uploads
- 🧪 **Test PDF Loader** for quick demos and development

### Advanced Features
- 📋 **Form Field Extraction** with ground truth comparison UI
  - Toggle between extraction-only and comparison views
  - Accuracy metrics (exact, similar, different matches)
  - Visual indicators for match quality
- 📊 **Enhanced Metadata** and validation
- 🎨 **Material Design UI** (MUI v7)
- ✨ **Modern Stack**
  - Python 3.11+ with latest type annotations
  - React 19.1 with TypeScript
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

**Security Tools:**
```bash
# Install pre-commit hooks
pre-commit install

# Run security scan
detect-secrets scan

# Scan for secrets in git history
gitleaks detect
```

**Security Features:**
- 🔒 Pre-commit hooks for secret detection
- 🔐 Environment variables for all configuration
- 🧹 Automatic log sanitization for sensitive data
- 🚫 No hardcoded credentials or API keys
- 📜 Git history cleaned of uploaded files
- 🛡️ Comprehensive `.gitignore` patterns

> ⚠️ **Important**: Git history was rewritten on 2025-01-21 to remove sensitive files. 
> Collaborators should re-clone the repository.

See [Security Policy](docs/SECURITY.md) for detailed guidelines.

## Documentation

📖 **Available Documentation:**
- [API Reference](docs/API.md) - Complete API endpoint documentation
- [Technical Guide](docs/TECHNICAL.md) - Setup and development guide
- [Contributing](docs/CONTRIBUTING.md) - Contribution guidelines
- [Security Policy](docs/SECURITY.md) - Security practices and reporting
- [Test Guide](tests/README.md) - Testing documentation
- [Technical Debt](docs/TECHNICAL_DEBT.md) - Known issues and improvements
- [Product Requirements](docs/PRD.md) - Detailed product specifications
- [Changelog](CHANGELOG.md) - Version history and changes

## Limitations

**Current Scope (POC):**
- ❌ No authentication/authorization
- 👤 Single user only
- 💾 Ephemeral storage (files cleared on restart)
- 📝 No PDF editing capabilities

See [Technical Debt](docs/TECHNICAL_DEBT.md) for planned improvements.

## Author

Created by Dominic Fahey (domfahey@gmail.com)

## License

MIT License - See [LICENSE](LICENSE) file for details
