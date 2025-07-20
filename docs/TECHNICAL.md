# Technical Guide

Combined technical documentation for development, deployment, and logging.

Author: Dominic Fahey (domfahey@gmail.com)  
License: MIT

## Development Setup

### Prerequisites
- Python 3.9+ with UV
- Node.js 18+
- Docker (optional)

### Quick Start

```bash
# Backend
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

### URLs
- Frontend: http://localhost:5173 (or 5174-5175 if port conflicts)
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Testing & Code Quality

```bash
# Tests
pytest                    # Backend (no tests currently)
cd frontend && npm test   # Frontend (39 tests passing)

# Code quality (zero errors/warnings)
cd backend && ruff check . && ruff format .  # Python
cd frontend && npm run lint && npm run format # TypeScript

# Type checking
cd backend && mypy .      # Python types
cd frontend && npx tsc --noEmit  # TypeScript
```

## Docker Deployment

### Quick Deploy

```bash
docker-compose up -d
```

### Environment Variables

```env
# Backend
LOG_LEVEL=DEBUG         # Default for development (DEBUG/INFO/WARNING/ERROR)
JSON_LOGS=false         # true for production JSON format
MAX_FILE_SIZE=52428800  # 50MB file upload limit

# Frontend 
VITE_API_BASE_URL=http://localhost:8000/api

# CORS (automatically configured for dev ports)
# Production: Set specific allowed origins
```

### Commands

```bash
docker-compose logs -f        # View logs
docker-compose down          # Stop
docker-compose build         # Rebuild
```

## Enhanced Logging System

### Features
- **Correlation IDs**: Auto-generated UUIDs for request tracing
- **Performance Timing**: Microsecond precision for all operations
- **Structured Output**: Rich console (dev) or JSON (production)
- **Debug Mode**: Enabled by default for development troubleshooting
- **API Logging**: Comprehensive request/response/error tracking

### Decorators & Utilities

```python
# API endpoint logging
@log_api_call("pdf_upload", log_params=True, log_response=True, log_timing=True)
@log_file_operation("pdf_upload", file_param="file", log_file_details=True)

# Manual logging
api_logger = APILogger("operation_name")
api_logger.log_request_received(...)
api_logger.log_processing_success(...)
```

### Output Examples

**Development:**
```
[13:32:47] INFO Request started
           method=POST url=/api/upload correlation_id=uuid-123
```

**Production (JSON):**
```json
{
  "timestamp": "2025-07-20T13:32:47Z",
  "level": "info",
  "message": "Request completed",
  "correlation_id": "uuid-123",
  "duration_ms": 145.23
}
```

## Project Structure

```
backend/
├── app/
│   ├── api/         # FastAPI endpoints with enhanced logging
│   ├── models/      # Pydantic v2 models with validation
│   ├── services/    # Business logic with performance tracking
│   ├── utils/       # Logging utilities & API decorators
│   ├── middleware/  # Request middleware & CORS
│   └── core/        # Configuration & logging setup
frontend/
└── src/
    ├── components/  # React components (TypeScript)
    ├── services/    # API client with error handling
    ├── hooks/       # Custom React hooks
    └── types/       # TypeScript type definitions
```

## Key Commands Reference

| Task | Command |
|------|---------|
| Install backend | `uv pip install -e ".[dev]"` |
| Run backend | `uvicorn app.main:app --reload` |
| Run frontend | `npm run dev` |
| Test all | `pytest && npm test` |
| Lint | `ruff check . && npm run lint` |
| Format | `ruff format . && npm run format` |
| Type check | `mypy . && npx tsc --noEmit` |
| Deploy | `docker-compose up -d` |

## Production Notes

### Configuration
- **Logging**: Set `JSON_LOGS=true` and `LOG_LEVEL=INFO` 
- **CORS**: Configure specific allowed origins (not localhost)
- **Storage**: Persistent volume for uploads directory
- **Proxy**: Reverse proxy with SSL termination
- **Limits**: Configure `MAX_FILE_SIZE` as needed (default 50MB)

### Monitoring & Debugging
- **Correlation IDs**: Track requests across services
- **Performance metrics**: Monitor upload/processing times
- **Error tracking**: Enhanced error responses with debug context
- **Health checks**: `/api/health` endpoint for load balancer probes

### Security Considerations
- **Input validation**: Pydantic v2 with enhanced security checks
- **File scanning**: Consider adding antivirus scanning for uploads
- **Rate limiting**: Implement in production environment
- **Authentication**: Add user auth for production use