# Technical Guide

## Setup

### Prerequisites
- Python 3.9+ with UV
- Node.js 18+
- Docker (optional)

### Install & Run

```bash
# Backend
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Docker
docker-compose up -d
```

URLs:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Development

```bash
# Tests
pytest && npm test
npx playwright test    # E2E

# Quality
ruff check . && ruff format .
npm run lint && npm run format
mypy . && npx tsc --noEmit

# Coverage
pytest --cov=backend
npm run test:coverage
```

## Project Structure

```
backend/
├── app/
│   ├── api/         # Endpoints
│   ├── models/      # Pydantic models
│   ├── services/    # Business logic
│   └── middleware/  # CORS, logging
frontend/
├── src/
│   ├── components/  # React components
│   ├── hooks/       # Custom hooks
│   └── services/    # API client
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

- Full-text PDF search
- URL loading support
- Form field extraction
- Virtual scrolling
- Material UI components

## Production Notes

- Enable JSON logs: `JSON_LOGS=true`
- Configure CORS for production domains
- Set up persistent storage for uploads