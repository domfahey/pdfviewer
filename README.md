# PDF Viewer POC

A modern, production-ready PDF viewer application with React 18+ frontend and FastAPI backend, featuring comprehensive logging, performance monitoring, and robust error handling.

## 🌟 Features

### PDF Viewer Capabilities
- **Advanced PDF Rendering** with PDF.js v5.3.93
- **Virtual Page Rendering** for optimal performance with large documents
- **Interactive Annotations** viewing and form field support
- **Full-Text Search** with highlighting
- **Thumbnail Navigation** with quick page jumping
- **Zoom Controls** (25% - 500%) with fit-to-page options
- **Keyboard Navigation** with standard shortcuts
- **Print & Download** capabilities
- **Metadata Display** with document properties

### Backend Features
- **Structured Logging** with correlation IDs and performance tracking
- **File Validation** with MIME type verification and size limits (50MB)
- **Secure Upload** with UUID-based file naming
- **Comprehensive Error Handling** with detailed logging
- **Health Monitoring** with service statistics
- **Production-Ready** JSON logging for monitoring

### Development Experience
- **Hot Module Replacement** with Vite
- **TypeScript** throughout for type safety
- **Comprehensive Testing** with pytest and Vitest
- **Code Quality** tools (ruff, black, mypy, ESLint)
- **Rich Console Logging** for development debugging

## 🏗️ Architecture

### Technology Stack
- **Frontend**: React 19.1 + TypeScript + Vite + PDF.js + Tailwind CSS
- **Backend**: FastAPI + Python 3.9+ + UV + structlog + rich
- **State Management**: Zustand for lightweight state management
- **Testing**: pytest + Vitest + Testing Library
- **Logging**: structlog + rich for development, JSON for production

### Project Structure
```
pdf-viewer/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── main.py            # Application entry point
│   │   ├── core/              # Core configuration
│   │   │   └── logging.py     # Centralized logging setup
│   │   ├── middleware/        # HTTP middleware
│   │   │   └── logging.py     # Request correlation & logging
│   │   ├── utils/             # Utility functions
│   │   │   └── logger.py      # Performance tracking & utilities
│   │   ├── api/               # API endpoints
│   │   ├── models/            # Pydantic data models
│   │   └── services/          # Business logic
│   │       └── pdf_service.py # PDF processing service
├── frontend/                   # React frontend application
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── PDFViewer/     # PDF viewer components
│   │   │   └── Upload/        # File upload components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API service layer
│   │   └── types/             # TypeScript type definitions
├── tests/                      # Backend test suite
├── uploads/                    # File storage (development)
├── pyproject.toml             # Backend dependencies & tools
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ with UV package manager
- Node.js 18+ with npm
- Git

### Backend Setup

```bash
# Clone the repository
git clone <repository-url>
cd pdf-viewer

# Install backend dependencies with UV
uv pip install -e ".[dev]"

# Start the backend server
cd backend
uvicorn app.main:app --reload --port 8000

# Backend will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Frontend Setup

```bash
# Install frontend dependencies
cd frontend
npm install

# Start the development server
npm run dev

# Frontend will be available at http://localhost:5173
```

### Environment Configuration

Create `.env` files for configuration:

**Backend (.env)**:
```bash
# Logging configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
JSON_LOGS=false                   # true for production JSON logs
ENVIRONMENT=development           # development, staging, production

# File upload settings
MAX_FILE_SIZE=52428800           # 50MB in bytes
UPLOAD_DIR=uploads               # Upload directory path
```

**Frontend (.env)**:
```bash
# API configuration
VITE_API_BASE_URL=http://localhost:8000/api
VITE_NODE_ENV=development
```

## 📚 API Documentation

### Endpoints

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| `POST` | `/api/upload` | Upload PDF file | `multipart/form-data` | `PDFUploadResponse` |
| `GET` | `/api/pdf/{file_id}` | Retrieve PDF file | - | `application/pdf` |
| `GET` | `/api/metadata/{file_id}` | Get PDF metadata | - | `PDFMetadata` |
| `DELETE` | `/api/pdf/{file_id}` | Delete PDF file | - | `{"success": true}` |
| `GET` | `/api/health` | Health check | - | `{"status": "healthy"}` |

### Data Models

**PDFUploadResponse**:
```typescript
{
  file_id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  metadata: PDFMetadata;
}
```

**PDFMetadata**:
```typescript
{
  title?: string;
  author?: string;
  subject?: string;
  creator?: string;
  producer?: string;
  creation_date?: string;
  modification_date?: string;
  page_count: number;
  file_size: number;
  encrypted: boolean;
}
```

## 🧪 Testing

### Backend Tests

```bash
# Run all backend tests
pytest

# Run with coverage
pytest --cov=backend/app --cov-report=html

# Run specific test file
pytest tests/test_upload.py -v

# Run tests with rich output
pytest -v --tb=short
```

### Frontend Tests

```bash
cd frontend

# Run all frontend tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### Test Structure

**Backend Test Coverage**:
- Unit tests for PDF service operations
- Integration tests for API endpoints
- Real-world PDF sample testing (EPA, Weblite, PrinceXML, Anyline, NHTSA)
- Error handling and edge cases
- Performance and memory testing

**Frontend Test Coverage**:
- Component rendering and interaction tests
- Custom hook functionality tests
- API service integration tests
- Error boundary and edge case tests

## 🔧 Development Tools

### Code Quality

```bash
# Run all quality checks
./check-all.sh

# Backend code quality
cd backend
ruff check .                     # Linting
black .                          # Formatting
mypy . --ignore-missing-imports  # Type checking

# Frontend code quality
cd frontend
npm run lint                     # ESLint
npm run format                   # Prettier
npm run type-check              # TypeScript
```

### Build Commands

```bash
# Backend build (for production)
cd backend
uv pip install -e .

# Frontend build
cd frontend
npm run build                    # Production build
npm run preview                  # Preview production build
```

## 📝 Logging & Monitoring

### Logging Features

The application includes comprehensive structured logging:

**Development Logging**:
- Rich console output with colors and formatting
- Request correlation IDs for tracing
- Performance metrics for all operations
- File operation logging with context
- Detailed error logging with stack traces

**Production Logging**:
- JSON structured logs for log aggregation
- Correlation IDs for distributed tracing
- Performance monitoring and metrics
- Error tracking with context
- Request/response logging

### Log Configuration

**Environment Variables**:
- `LOG_LEVEL`: Set logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `JSON_LOGS`: Enable JSON format for production (`true`/`false`)
- `ENVIRONMENT`: Set environment context (development, staging, production)

**Example Log Output** (Development):
```
[13:32:46] INFO     PDF service initialized
           upload_dir=uploads max_file_size_mb=50.0
           [app.services.pdf_service]

[13:32:47] INFO     Request started
           method=POST url=http://localhost:8000/api/upload
           correlation_id=uuid-1234 [app.middleware.logging]

[13:32:48] INFO     File upload completed
           file_id=abc-123 filename=document.pdf duration_ms=145.23
           [app.services.pdf_service]
```

## 🚀 Deployment

### Docker Deployment (Recommended)

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv pip install -e .
COPY backend/ ./backend/
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY frontend/package*.json .
RUN npm ci
COPY frontend/ .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]
```

### Production Configuration

**Backend Environment**:
```bash
LOG_LEVEL=INFO
JSON_LOGS=true
ENVIRONMENT=production
MAX_FILE_SIZE=52428800
```

**Frontend Environment**:
```bash
VITE_API_BASE_URL=https://your-api-domain.com/api
VITE_NODE_ENV=production
```

## 🤝 Contributing

### Development Workflow

1. **Fork and Clone**: Fork the repository and clone locally
2. **Create Branch**: Create feature branch from `main`
3. **Install Dependencies**: Run `uv pip install -e ".[dev]"` and `npm install`
4. **Make Changes**: Implement your feature or fix
5. **Run Tests**: Ensure all tests pass with `pytest` and `npm test`
6. **Quality Checks**: Run `./check-all.sh` for code quality verification
7. **Commit**: Use conventional commit messages
8. **Pull Request**: Submit PR with clear description

### Code Standards

- **Python**: Follow PEP 8, use type hints, document with docstrings
- **TypeScript**: Use strict mode, proper typing, functional components
- **Testing**: Maintain >90% test coverage for new features
- **Logging**: Use structured logging with appropriate context
- **Documentation**: Update docs for new features or API changes

## 📋 Project Status

- ✅ **Phase 1**: Basic PDF upload and viewing functionality
- ✅ **Phase 2**: Advanced navigation, zoom controls, and metadata display
- ✅ **Logging Infrastructure**: Comprehensive structured logging system
- 🔄 **Phase 3**: Advanced features (annotations, search, forms) - In Progress
- 📋 **Phase 4**: Production deployment and monitoring - Planned

## 📖 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://react.dev/
- **PDF.js Documentation**: https://mozilla.github.io/pdf.js/
- **Structlog Documentation**: https://www.structlog.org/
- **UV Documentation**: https://github.com/astral-sh/uv

## 📄 License

This project is a proof of concept for educational and demonstration purposes. See individual dependencies for their respective licenses.

---

**Built with ❤️ using modern web technologies and best practices.**