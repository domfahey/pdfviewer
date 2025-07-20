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
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Testing & Code Quality

```bash
# Tests
pytest                    # Backend
cd frontend && npm test   # Frontend

# Code quality
ruff check . && black .   # Python
npm run lint             # TypeScript
```

## Docker Deployment

### Quick Deploy

```bash
docker-compose up -d
```

### Environment Variables

```env
# Backend
LOG_LEVEL=INFO
LOG_FORMAT=json         # For production
MAX_FILE_SIZE=52428800

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api
```

### Commands

```bash
docker-compose logs -f        # View logs
docker-compose down          # Stop
docker-compose build         # Rebuild
```

## Logging Configuration

### Features
- **Correlation IDs**: Track requests via `X-Correlation-ID`
- **Performance Timing**: Automatic operation metrics
- **Structured Output**: JSON (prod) or console (dev)

### Decorators

```python
@log_api_call("operation_name")      # API operations
@log_file_operation("file_upload")   # File operations
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
│   ├── api/         # Endpoints
│   ├── models/      # Pydantic models
│   ├── services/    # Business logic
│   ├── utils/       # Logging utilities
│   └── middleware/  # Request middleware
frontend/
└── src/
    ├── components/  # React components
    └── services/    # API client
```

## Key Commands Reference

| Task | Command |
|------|---------|
| Install backend | `uv pip install -e ".[dev]"` |
| Run backend | `uvicorn app.main:app --reload` |
| Run frontend | `npm run dev` |
| Test all | `pytest && npm test` |
| Format | `black . && npm run format` |
| Deploy | `docker-compose up -d` |

## Production Notes

- Enable JSON logging: `LOG_FORMAT=json`
- Configure persistent storage for uploads
- Set up reverse proxy with SSL
- Monitor logs for correlation IDs
- File size limit: 50MB (configurable)