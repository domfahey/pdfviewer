# CLAUDE.md

Guidance for Claude Code when working with this PDF Viewer POC.

## Project Overview

PDF viewer POC with React/FastAPI. Features include full-text search, URL loading, and form extraction.

## Tech Stack

**Frontend:** React 19.1, TypeScript, Material UI v7, PDF.js  
**Backend:** FastAPI, Python 3.11+, UV, Pydantic v2  
**Code Quality:** Modern Python syntax (X | Y unions, datetime.UTC), optimized React patterns

## Key Requirements

- Full-text PDF search with highlighting
- URL loading support for remote PDFs
- Ground truth comparison UI with accuracy metrics
- 50MB file size limit
- Correlation ID propagation
- Zero linting/type errors

## Quick Reference

See [Technical Guide](docs/TECHNICAL.md) for:
- Setup commands
- Testing & quality checks
- Project structure
- Environment variables

## API Decorators

```python
@log_api_call("operation", log_params=True, log_response=True)
@log_file_operation("upload", file_param="file")
```

## Development Notes

- React 19 Strict Mode compatibility
- Pydantic v2 computed fields and validators
- Debug logging enabled by default
- CORS configured for ports 5173-5176

## Important Files

- `backend/app/api/load_url.py` - URL loading endpoint
- `frontend/src/hooks/usePDFSearch.ts` - Search functionality
- `frontend/src/components/TestPDFLoader.tsx` - Test PDF loader

Author: Dominic Fahey (domfahey@gmail.com)  
License: MIT