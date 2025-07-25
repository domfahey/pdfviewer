# Changelog

All notable changes to the PDF Viewer POC will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Python 3.11+ modernization**:
  - Updated minimum Python version from 3.9 to 3.11
  - Modern union syntax (`X | Y`) throughout codebase
  - Direct use of `datetime.UTC` constant
  - Updated `isinstance` calls to use union types
- **React component optimization**:
  - Moved mock data outside components to prevent recreations
  - Improved performance with referential equality
- **Enhanced ground truth comparison UI**:
  - Fully functional toggle between extraction and comparison views
  - Real-time accuracy metrics calculation (75% overall accuracy)
  - Visual indicators for match quality (exact, similar, different, no truth)
  - Overall accuracy percentage with color-coded progress bar
  - Detailed accuracy breakdown by category (personal, business, dates, financial)
  - Mock data optimization moved outside component for performance
- **Full-text PDF search** with highlighting and navigation
- **URL loading endpoint** (`/api/load-url`) to load PDFs from web URLs
- **Test PDF loader** component for quick access to sample PDFs
- **Search navigation controls** with next/previous buttons and keyboard shortcuts (F3/Shift+F3)
- **PDFSearchHighlight** component for visual search results
- **usePDFSearch** hook for managing search functionality
- **Comprehensive test infrastructure**:
  - Unit, integration, and E2E test suites
  - Test documentation and best practices guide
  - Performance and load testing capabilities
  - Test coverage reporting with 80% threshold
  - Smoke tests for quick validation
- **Makefile** with developer commands:
  - `make lint`, `make format`, `make type` for code quality
  - `make test-*` commands for different test categories
  - `make qa` for full quality assurance
  - `make help` for command documentation
- **Type safety improvements**:
  - Updated to require Python 3.11+ minimum version
  - Added type annotations to critical functions
  - Configured mypy with appropriate overrides
- **Security enhancements**:
  - Pre-commit hooks for secret detection (detect-secrets, gitleaks)
  - Comprehensive `.gitignore` with security patterns
  - `.env.example` template for safe configuration
  - CONTRIBUTING.md with security checklist
  - Removed all uploaded PDFs from git history
  - Cleaned Python cache files from repository
- **Test PDF fixtures** and sample files
- Extended CORS support to ports 5173-5176
- Search match counter showing "X of Y" results
- Comprehensive Pydantic v2 validation with computed fields
- Enhanced metadata with complexity scoring and document categorization
- Upload status tracking and processing priority calculation
- File size validation with POC-specific constraints
- UUID v4 pattern validation for file IDs
- Path traversal protection in filename validation
- Timezone-aware datetime handling
- Storage efficiency metrics
- Debug information in error responses
- API logging utility module with microsecond precision
- Material Design UI with MUI v7 components
- Sticky PDF controls toolbar
- Fit mode functionality (width, height, page)
- View mode toggle (Original PDF / Digital Markdown)
- Extracted fields panel for form data display (preview UI)
- Ground truth comparison mode with accuracy metrics
- Author attribution and MIT licensing
- Documentation updates for POC best practices (2025-01-21)

### Changed
- Upgraded to Pydantic v2 with enhanced model validation
- Improved error responses with `_debug` context
- Refactored PDF viewer for React 19 compatibility
- Updated all documentation to be more concise (86% reduction)
- Consolidated documentation from 7 files to 4 files
- Fixed all TypeScript and Python linting issues
- Enhanced logging with request/response tracking
- Upgraded from React 18 to React 19.1
- Updated performance test thresholds for real-world PDFs (60s for image-heavy, 30s for standard)
- **BREAKING**: Rewritten git history to remove sensitive files (collaborators must re-clone)
- Added automatic `python-magic-bin` installation for Windows compatibility

### Fixed
- React double-rendering issues in Strict Mode
- CORS configuration for frontend development
- Type checking errors in TypeScript and mypy
- Updated minimum Python version to 3.11+ for modern features
- All backend type errors (139 → 0)
- Failing tests in PDFThumbnails component
- Integration test failures for PDF workflows
- Coverage reporting configuration
- Upload progress UI race conditions
- PDF rendering cleanup on component unmount
- Browser compatibility issues
- Restored PDFExtractedFields panel that was accidentally removed

## [0.1.0] - 2025-07-20

### Added
- Initial POC release with core PDF viewing functionality
- React 18+ frontend with PDF.js integration
- FastAPI backend with file upload and metadata extraction
- Virtual page rendering for performance optimization
- Comprehensive structured logging infrastructure
- API logging decorators for monitoring
- Correlation ID tracking across requests
- Rich console output for development
- JSON logging for production environments
- Docker deployment configuration
- Comprehensive test suite with real PDF samples
- API documentation with OpenAPI/Swagger

### Features
- PDF upload with validation (50MB limit)
- Page navigation and zoom controls (25%-500%)
- Thumbnail sidebar navigation
- PDF metadata display
- Print and download capabilities
- Keyboard shortcuts support
- Error boundaries and graceful error handling

### Known Limitations (POC)
- No authentication/authorization
- Single-user file storage
- No persistent storage (uploads cleared on restart)
- Limited to PDF files only
- No annotation editing capabilities
- Search functionality not yet implemented