# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modern PDF viewer proof of concept featuring a React 18+ frontend with FastAPI backend. The application uses PDF.js for document rendering and focuses on performance optimization for large documents.

## Architecture

**Frontend Stack:**
- React 18+ with TypeScript and Vite build system
- PDF.js integration with web workers for performance
- Virtual page rendering (only visible pages loaded)
- Tailwind CSS for styling

**Backend Stack:**
- FastAPI with Python 3.9+ and UV dependency management
- Async file upload and processing
- PDF metadata extraction
- Auto-generated OpenAPI documentation

## Development Commands

Since this is a new project, standard commands will be:

**Frontend (when implemented):**
```bash
npm install                 # Install dependencies
npm run dev                # Start development server
npm run build              # Build for production
npm run lint               # Run ESLint
npm run typecheck          # TypeScript checking
```

**Backend (when implemented):**
```bash
uv venv                    # Create virtual environment
uv pip install -r requirements.txt  # Install dependencies
uvicorn main:app --reload  # Start development server
pytest                    # Run tests
ruff check . && ruff format .  # Linting and formatting
black .                    # Code formatting
```

## Key Implementation Requirements

**PDF.js Integration:**
- Use exact version matching between pdf.js and pdf.worker.js
- Implement virtual scrolling to render only visible pages
- Configure web workers for performance (mandatory)
- Use HTTP Range Requests for partial PDF loading
- Implement proper page cleanup when scrolling

**Performance Considerations:**
- Limit concurrent page renders to 3-5 pages maximum
- Use `page.cleanup()` method for non-visible pages
- Clear browser cache when updating PDF.js versions
- Support web-optimized PDFs (150 DPI, JPEG encoding)

**Cross-Domain and Security:**
- Configure CORS headers for external PDF URLs
- Implement PDF URL validation and sanitization
- Use Content Security Policy (CSP) headers
- Validate PDF file signatures before processing

## Project Structure (Planned)

```
frontend/
├── src/
│   ├── components/PDFViewer/    # Main PDF rendering components
│   ├── hooks/                  # PDF document and upload hooks
│   └── services/api.ts         # Backend API communication

backend/
├── app/
│   ├── api/                    # FastAPI route handlers
│   ├── models/                 # Pydantic models
│   └── services/               # PDF processing services
```

## Development Notes

- Follow test-driven development (TDD) practices
- Implement error boundaries for PDF rendering failures
- Monitor memory usage during development
- Test across all target browsers with cache clearing
- Store prompts in YAML files in `/prompts` directory (as per global config)