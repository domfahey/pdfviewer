# agents.md

This file provides guidance for AI agents working with this PDF viewer proof of concept project.

## Project Context

Modern PDF viewer POC with React 19.1 frontend and FastAPI backend, emphasizing PDF.js performance optimization, virtual page rendering, and ground truth comparison UI.

## Key Technical Requirements

**PDF.js Performance:**
- Virtual page rendering (visible pages only)
- Web worker configuration mandatory
- Exact version matching pdf.js/pdf.worker.js
- HTTP Range Requests for large files

**Development Stack:**
- Frontend: React 19.1, TypeScript, Vite, Material-UI v7
- Backend: FastAPI, Python 3.11+, UV dependencies, modern syntax (X | Y unions)
- Testing: pytest, TDD practices
- Linting: ruff, black formatting

**Memory Management:**
- Limit 3-5 concurrent page renders
- Implement page.cleanup() for non-visible pages
- Monitor memory usage during development

**Security Considerations:**
- CORS configuration for external PDFs
- PDF file validation and sanitization
- CSP headers implementation

Refer to PRD.md for complete specifications and CLAUDE.md for development commands.