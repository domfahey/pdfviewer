# Technical Debt

This document tracks potential improvements and refactoring opportunities for the PDF Viewer POC.

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
- Documentation mentions Docker but no Docker files exist
- `docker-compose up -d` command referenced but not implemented

**Proposed Solution:**
- Create `Dockerfile` for backend and frontend
- Create `docker-compose.yml` for full stack
- Include libmagic in Docker image (or implement header check first)

---

### 3. CI/CD Pipeline

**Current State:**
- No automated testing in CI/CD
- Manual testing required before deployment

**Proposed Solution:**
- GitHub Actions workflow for testing
- Automated security scanning
- Deploy previews for PRs

---

## Completed Improvements

- ✅ Comprehensive test infrastructure
- ✅ Type safety improvements
- ✅ Security enhancements and git cleanup
- ✅ Documentation consolidation
- ✅ Ground truth comparison UI for extracted fields