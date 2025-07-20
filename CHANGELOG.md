# Changelog

All notable changes to the PDF Viewer POC will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-20

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