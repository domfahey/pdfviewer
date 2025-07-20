# API Reference

PDF Viewer API endpoints for file management and metadata extraction.

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
- Max size: 50MB
- Returns: `file_id`, `filename`, `metadata`

### Get PDF File
```http
GET /api/pdf/{file_id}
```
Returns the PDF file for download.

### Get PDF Metadata
```http
GET /api/metadata/{file_id}
```
Returns extracted PDF metadata including:
- `page_count`, `file_size`, `title`, `author`
- `creation_date`, `encrypted` status

### Delete PDF
```http
DELETE /api/pdf/{file_id}
```
Permanently deletes the PDF file.

## Request Headers
- `X-Correlation-ID`: Optional UUID for request tracing

## Response Format

### Success Response
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "file_size": 1048576,
  "metadata": {
    "page_count": 10,
    "title": "Sample Document"
  }
}
```

### Error Response
```json
{
  "detail": "File not found",
  "status_code": 404
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

## Rate Limits
No rate limits implemented for POC.

## Authentication
No authentication required for POC.