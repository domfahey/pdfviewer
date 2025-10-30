# TODO - Bug Fixes

## Work Remaining (2025-11-01)
- Re-run backend `uv run pytest` once the uv cache permission issue is cleared; confirm upload-flow tests now pass.
- Re-run frontend vitest suite to verify the VirtualPDFViewer changes and address existing timeouts.

## Recently Discovered Issues (2025-10-30)

### Test Failures (Automated Runs)
- **Backend pytest:** `uv run pytest` aborts with 0 tests collected; coverage plugin reports 0% (below fail-under=80).
- **Frontend vitest:** `npm test` times out; `useFileUpload` tests "should set uploading state during upload" and "should track upload progress" exceed the 5000ms default timeout.

### Backend Linting Issues (100+ ruff errors)
- **Import ordering**: E402 errors in `app/api/load_url.py` (6 occurrences) - imports after constants
- **Import sorting**: I001 in `app/api/pdf.py` - unsorted import block
- **Unused imports**: `app/core/logging.py:209` (performance_logger), `app/models/pdf.py:8` (re)
- **Deprecated imports**: UP035 in `app/dependencies.py:3` - use `collections.abc.Callable`
- **Whitespace issues**: 50+ W291/W293 errors across multiple files (dependencies.py, middleware/logging.py, models/pdf.py, services/pdf_service.py, utils/api_logging.py, utils/decorators.py, utils/http_client.py, utils/validation.py)

### Backend Type Checking Issues (11 mypy errors)
- **Decorator type issues**: `app/utils/decorators.py:88` - await type incompatibility
- **Unused type ignore**: `app/utils/decorators.py:115`
- **Logger configuration**: `app/core/logging.py:55,75` - incompatible processors types
- **PDF service null handling**: `app/services/pdf_service.py:285,296,305` - filename can be None
- **Missing annotations**: `app/services/pdf_service.py:99` - function missing return/argument types

### Test Setup Issues
- **Missing system dependency**: libmagic required for python-magic (backend tests fail)
- **Makefile path issues**: cd .. commands incorrect, causing lint/test failures
- **Frontend test failures**: 19 eslint errors, memory issues, PDF service mock problems

## Backend Issues

### Critical - Type Errors (52 mypy errors)

1. **Missing TypeVar import** - `app/utils/validation.py:19`
   - Missing: `from typing import TypeVar`
   - Error: `Name "TypeVar" is not defined`

2. **Type incompatibilities in decorators** - `app/utils/decorators.py:88`
   - Incompatible types in "await" (actual type "R", expected type "Awaitable[Any]")

3. **Missing type annotations in middleware/logging.py**
   - Lines: 35, 42, 85, 200, 302, 320, 349, 367, 380, 384, 401, 421
   - Missing function type annotations and arguments

4. **Type incompatibilities in api_logging.py**
   - Line 94: Incompatible assignment (expression has type "dict[str, Any]", target has type "str | None")
   - Missing type annotations on lines: 45, 66, 68, 145, 162, 164, 298, 318, 322, 326, 330, 334, 338, 342, 352, 356, 370, 376

5. **Type errors in services/pdf_service.py**
   - Line 285: Argument "filename" has incompatible type "str | None"; expected "str"
   - Line 296: Argument 2 to "upload_completed" incompatible type "str | None"; expected "str"
   - Line 305: Argument "filename" incompatible type "str | None"; expected "str"

6. **Logger type errors** - `app/utils/logger.py`
   - Line 126: Missing return type annotation
   - Line 149: Missing type annotation

7. **structlog configuration issues** - `app/core/logging.py`
   - Lines 55, 75: Incompatible "processors" argument types

### High Priority - Linting Errors (78 ruff errors)

1. **Import ordering issues** - `app/api/load_url.py:13-18`
   - E402: Module level import not at top of file (6 occurrences)
   - Imports after constant definitions

2. **Import sorting** - `app/api/pdf.py:6`
   - I001: Import block is un-sorted or un-formatted

3. **Unused imports**
   - `app/core/logging.py:209` - F401: Unused `performance_logger`
   - `app/models/pdf.py:8` - F401: Unused `import re`

4. **Deprecated imports** - `app/dependencies.py:3`
   - UP035: Import `Callable` from `collections.abc` instead of `typing`

5. **Whitespace issues** (50+ occurrences)
   - W291: Trailing whitespace
   - W293: Blank lines contain whitespace
   - Files affected: dependencies.py, middleware/logging.py, models/pdf.py, services/pdf_service.py, utils/api_logging.py, utils/decorators.py, utils/http_client.py, utils/validation.py

### Critical - Missing Tests

- No backend tests directory exists
- Expected location: `backend/tests/`
- Need pytest configuration fix (coverage plugin issue)

## Frontend Issues

### Critical - Test Failures (28 failures)

#### Memory Issues
1. **JavaScript heap out of memory**
   - Fatal error during test execution
   - FATAL ERROR: Ineffective mark-compacts near heap limit
   - Likely memory leak in tests

#### Missing Test Setup (12 failures)
2. **IntersectionObserver not defined** - All PDFThumbnails tests
   - `ReferenceError: IntersectionObserver is not defined`
   - Needs mock in test setup
   - Affected: `src/components/__tests__/PDFThumbnails.test.tsx`
   - All 12 PDFThumbnails tests failing

#### PDF Service Failures (8 failures)
3. **PDF rendering errors** - `src/services/__tests__/pdfService.test.ts`
   - `getPage` test failing: "Failed to load page 1"
   - `renderPageToCanvas` tests failing: "Failed to render page"
   - Mock PDF.js objects not properly configured
   - Tests affected:
     - should successfully get a page from document
     - should successfully render page to canvas
     - should apply custom scale
     - should handle missing canvas context
     - should prevent concurrent renders on same canvas
     - should cancel existing render task
     - should handle RenderingCancelledException gracefully
     - should clear canvas before rendering

#### Upload Hook Issues (2 failures)
4. **Test timeouts** - `src/hooks/__tests__/useFileUpload.test.ts`
   - "Test timed out in 5000ms"
   - Tests affected:
     - should set uploading state during upload
     - should track upload progress

#### Component Rendering Issues (5 failures)
5. **PDFExtractedFields component** - `src/components/__tests__/PDFExtractedFields.test.tsx`
   - Missing phone number in rendered output
   - Missing confidence score "80%"
   - Missing field count "3"
   - Missing "Export to CSV/JSON" text
   - Missing "Phone" label
   - Component not rendering complete mock data

#### Search Hook Issues (1 failure)
6. **usePDFSearch** - `src/hooks/__tests__/usePDFSearch.test.ts`
   - `isSearching` state not being set correctly
   - Expected true, received false

### Unhandled Errors
- 4 unhandled promise rejections during test run
- Causing false positives in tests
- Related to PDF rendering cancellation

## Recommended Fixes Priority

### High Priority (Blocking)
1. Fix backend TypeVar import
2. Fix backend import ordering (E402 errors)
3. Add IntersectionObserver mock to frontend test setup
4. Fix PDF.js mocks in pdfService tests
5. Fix memory leak in frontend tests

### Medium Priority
1. Add missing type annotations (backend)
2. Fix whitespace issues (auto-fixable with `--fix`)
3. Fix component rendering in PDFExtractedFields tests
4. Fix useFileUpload timeout issues

### Low Priority
1. Remove unused imports
2. Update deprecated imports (Callable)
3. Create backend tests directory
4. Fix pytest coverage configuration

## Commands to Run

### Backend Auto-fixes
```bash
cd backend
uv run ruff check . --fix  # Fix auto-fixable issues
uv run black .              # Format code
uv run mypy .               # Recheck types
```

### Frontend
```bash
cd frontend
npm test -- --run           # Run tests again after fixes
```
