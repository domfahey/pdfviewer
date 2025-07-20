# API Reference

PDF Viewer API endpoints with enhanced Pydantic v2 validation and comprehensive logging.

Author: Dominic Fahey (domfahey@gmail.com)  
License: MIT

## Base URL
- Development: `http://localhost:8000/api`
- OpenAPI Docs: `http://localhost:8000/docs`

## Endpoints

### Health Check
```http
GET /api/health
```
Returns system health status and storage availability.

### Upload PDF
```http
POST /api/upload
Content-Type: multipart/form-data

file: <pdf_file>
```
- **Max size:** 50MB (configurable via MAX_FILE_SIZE)
- **Validation:** Enhanced Pydantic v2 with security checks
- **Returns:** Enhanced response with computed fields and POC metadata
- **Logging:** Comprehensive request/response logging with correlation IDs

### Get PDF File
```http
GET /api/pdf/{file_id}
```
Returns the PDF file for download.

### Get PDF Metadata
```http
GET /api/metadata/{file_id}
```
Returns enhanced PDF metadata with:
- **Basic:** `page_count`, `file_size`, `title`, `author`, `encrypted`
- **Dates:** `creation_date`, `modification_date` (timezone-aware)
- **Computed:** `file_size_mb`, `document_complexity_score`, `document_category`
- **Validation:** Path traversal protection, content sanitization

### Delete PDF
```http
DELETE /api/pdf/{file_id}
```
Permanently deletes the PDF file.

## Request Headers
- `X-Correlation-ID`: Optional UUID for request tracing and debugging
- `Origin`: Required for CORS validation (dev: localhost:5173-5175)

## Response Format

### Enhanced Upload Response (Pydantic v2)
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "file_size": 1048576,
  "file_size_mb": 1.0,
  "mime_type": "application/pdf",
  "upload_time": "2025-07-20T16:30:00Z",
  "upload_age_hours": 0.0,
  "upload_status": "fresh",
  "processing_priority": "normal",
  "metadata": {
    "title": "Sample Document",
    "author": "John Doe",
    "page_count": 10,
    "file_size": 1048576,
    "file_size_mb": 1.0,
    "encrypted": false,
    "document_complexity_score": 35.5,
    "document_category": "short-document",
    "is_large_document": false
  },
  "_poc_info": {
    "serialized_at": "2025-07-20T16:30:00Z",
    "model_version": "2.0",
    "enhanced_validation": true
  }
}
```

### Enhanced Error Response
```json
{
  "error": "File validation failed",
  "detail": "File size exceeds POC limit of 50MB",
  "error_code": "FILE_SIZE_EXCEEDED",
  "timestamp": "2025-07-20T16:30:00Z",
  "_debug": {
    "error_type": "validation",
    "has_detail": true,
    "has_error_code": true,
    "severity": "medium"
  }
}
```

## Status Codes
- `200`: Success
- `400`: Bad request (invalid input)
- `404`: Resource not found
- `413`: File too large
- `500`: Server error

## Example Usage

```bash
# Upload PDF
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf"

# Get metadata
curl http://localhost:8000/api/metadata/{file_id}

# Download PDF
curl http://localhost:8000/api/pdf/{file_id} -o output.pdf
```

## Validation & Security Features

### Enhanced Pydantic v2 Validation
- **File validation:** Size limits, MIME type verification, path traversal protection
- **UUID validation:** Strict UUID v4 format enforcement with pattern matching
- **Date validation:** Timezone-aware datetime handling, future date prevention
- **Text sanitization:** Control character filtering, metadata field validation
- **POC constraints:** Document complexity scoring, processing priority assignment

### CORS Configuration
- **Allowed origins:** `localhost:3000`, `localhost:5173-5175` for development
- **Methods:** All HTTP methods supported
- **Headers:** Full header support for development

### Logging & Monitoring
- **Correlation IDs:** Automatic request tracking across all endpoints
- **Performance metrics:** Request duration, file operation timing
- **Debug mode:** Enhanced logging enabled by default for development
- **Error tracking:** Comprehensive error context and stack traces

## Rate Limits
No rate limits implemented for POC.

## Authentication  
No authentication required for POC.