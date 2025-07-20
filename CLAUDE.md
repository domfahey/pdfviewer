# CLAUDE.md

Guidance for Claude Code when working with this PDF Viewer POC.

Author: Dominic Fahey (domfahey@gmail.com)  
License: MIT

## Project Overview

PDF viewer POC with React/PDF.js frontend and FastAPI backend. Focus on performance with virtual page rendering and structured logging.

## Tech Stack

**Frontend:**
- React 18, TypeScript, Vite
- PDF.js with web workers
- Tailwind CSS

**Backend:**
- FastAPI, Python 3.9+, UV
- Structured logging (structlog)
- Correlation ID tracking

## Commands

```bash
# Backend
uv pip install -e ".[dev]"
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Docker
docker-compose up -d

# Tests
pytest && npm test

# Logging
LOG_LEVEL=DEBUG LOG_FORMAT=console  # Development
LOG_FORMAT=json                     # Production
```

## Key Requirements

- Virtual scrolling (render only visible pages)
- Web workers mandatory for PDF.js
- 50MB file size limit
- UUID-based file IDs
- Correlation ID propagation

## Project Structure

```
backend/app/
├── api/              # Endpoints
├── models/           # Pydantic models  
├── services/         # Business logic
├── utils/            # Logging decorators
└── middleware/       # Request correlation

frontend/src/
├── components/       # React components
└── services/        # API client
```

## API Decorators

```python
@log_api_call("operation")      # General API logging
@log_file_operation("upload")   # File-specific logging
```

## Development Notes

- Follow TDD practices
- Use error boundaries for PDF rendering
- Clear cache when updating PDF.js
- Test with real PDF samples in tests/