# Technical Debt

This document tracks potential improvements and refactoring opportunities for the PDF Viewer POC.

## Table of Contents

- [Future Improvements](#future-improvements)
  - [1. Replace libmagic Dependency](#1-replace-libmagic-dependency)
  - [2. Docker Configuration](#2-docker-configuration)
  - [3. CI/CD Pipeline](#3-cicd-pipeline)
- [Completed Improvements](#completed-improvements)

## Future Improvements

### 1. Replace libmagic Dependency

**Current State:**
- The backend uses `python-magic` (which requires system library `libmagic`) for MIME type verification
- This adds a system dependency that complicates installation, especially on Windows
- Located in `backend/app/services/pdf_service.py` line 250

**Problem:**
- Requires system package installation (`brew install libmagic`, `apt-get install libmagic1`, etc.)
- Can cause installation failures if libmagic is not present
- Adds complexity for a simple file type check

**Proposed Solution:**
Replace libmagic with a simple PDF header check:

```python
def validate_pdf_header(file_path: Path) -> bool:
    """Check if file has valid PDF header."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            # PDF files start with "%PDF-" followed by version
            return header.startswith(b'%PDF-')
    except Exception:
        return False
```

**Benefits:**
- ✅ No system dependencies
- ✅ Simpler installation process
- ✅ Cross-platform compatibility without extra steps
- ✅ Sufficient security when combined with extension check

**Trade-offs:**
- ❌ Less sophisticated than libmagic
- ❌ Won't detect corrupted PDFs as effectively
- ❌ May miss some edge cases that libmagic would catch

**Implementation Notes:**
1. Replace `magic.from_file()` call with header check
2. Remove `python-magic` from dependencies
3. Update documentation to remove libmagic installation steps
4. Add unit tests for header validation

**Priority:** Low - Current solution works, this is an optimization

---

### 2. Docker Configuration

**Current State:**
- Makefile has docker commands but no Docker files exist (docker-compose.yml, Dockerfile)
- `make docker-up` command available but requires docker-compose.yml

**Proposed Solution:**
- Create `Dockerfile` for backend and frontend
- Create `docker-compose.yml` for full stack
- Include libmagic in Docker image (or implement header check first)

**Priority:** Medium - Nice to have for easier deployment and development environment consistency

---

### 3. CI/CD Pipeline

**Current State:**
- No GitHub Actions workflows directory (.github/workflows/)
- Manual testing required before deployment
- Quality checks run via Makefile only

**Proposed Solution:**
- GitHub Actions workflow for automated testing on PRs
- Automated security scanning (CodeQL, dependency scanning)
- Deploy previews for PRs
- Automated documentation updates

**Priority:** Medium - Valuable for team collaboration and code quality

---

## Completed Improvements

### Recent (October 2025)
- ✅ **Code refactoring** - Removed 507 lines of overly complicated code (PR #31)
  - Simplified Pydantic models, removed unnecessary computed fields
  - Consolidated duplicate logging logic
  - Removed complex custom serializers
- ✅ **Performance optimizations** - Major improvements across frontend and backend
  - PDF thumbnail caching and lazy loading (70-99% improvement)
  - Search result caching (99% improvement on repeated searches)
  - Chunked file uploads (98% memory reduction)
  - Canvas rendering optimizations

### Previous Work
- ✅ Comprehensive test infrastructure (unit, integration, E2E)
- ✅ Type safety improvements (Python 3.11+ syntax, TypeScript strict mode)
- ✅ Security enhancements and git cleanup
- ✅ Documentation consolidation
- ✅ Ground truth comparison UI for extracted fields