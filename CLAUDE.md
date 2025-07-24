# CLAUDE.md

Guidance for Claude Code when working with this PDF Viewer POC.

## Project Overview

Production-ready PDF viewer POC with React 19.1/FastAPI. Features zero-error code quality, comprehensive test infrastructure, and advanced developer tooling.

## Tech Stack

**Frontend:** React 19.1, TypeScript, Material UI v7, PDF.js  
**Backend:** FastAPI, Python 3.11+, UV, Pydantic v2  
**Code Quality:** Zero linting errors, strict type checking, comprehensive test infrastructure

## Key Requirements

- **Git**: Use `main` branch (NOT `master`) for all development
- **Code Quality**: Zero linting errors (ESLint, Ruff), strict type checking (mypy, tsc)
- **Testing**: 99% backend pass rate, helper patterns, comprehensive coverage
- Full-text PDF search with highlighting
- URL loading support for remote PDFs
- Ground truth comparison UI with accuracy metrics
- 50MB file size limit, correlation ID propagation
- Security: Pre-commit hooks, no secrets in code
- System dependency: libmagic (see README)

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

- **Quality Pipeline**: `make qa` runs lint, format, type, test (all pass)
- **React 19**: Strict Mode compatibility, zero ESLint errors
- **Python 3.11+**: Modern syntax (X | Y unions), zero mypy errors
- **Testing**: Helper patterns reduce duplication by 30-40%
- **Pydantic v2**: Computed fields and validators
- **Debug logging**: Enabled by default with correlation IDs
- **CORS**: Configured for ports 5173-5176

## Git Workflow

🔄 **Recommended Ongoing Process:**
1. Create feature branch from `main`
2. Develop and test the feature
3. Create PR to merge into `main`
4. Delete branch immediately after merge
5. Repeat for next feature

**Branch Management:**
- **Primary Branch**: `main` (NOT `master`) - GitHub default branch
- Use only `main` as primary branch (consolidated from master/main in July 2025)
- All feature branches should branch from and merge back to `main`
- Delete merged feature branches immediately
- Keep branch lists clean and minimal
- Use short-lived feature branches (days/weeks, not months)

## Important Files

- `backend/app/api/load_url.py` - URL loading endpoint
- `frontend/src/hooks/usePDFSearch.ts` - Search functionality
- `frontend/src/components/TestPDFLoader.tsx` - Test PDF loader
- `frontend/src/components/PDFViewer/PDFExtractedFields.tsx` - Form extraction UI

Author: Dominic Fahey (domfahey@gmail.com)  
License: MIT