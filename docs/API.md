# API Reference

Base URL: `http://localhost:8000/api`

## Interactive Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

### Upload PDF
```
POST /api/upload
```
Upload PDF file (max 50MB). Returns file_id and metadata.

### Load from URL
```
POST /api/load-url
Body: {"url": "https://example.com/file.pdf"}
```
Download and process PDF from URL.

### Get PDF
```
GET /api/pdf/{file_id}
```
Download PDF file.

### Get Metadata
```
GET /api/metadata/{file_id}
```
Returns page count, file size, complexity score, document category.

### Delete PDF
```
DELETE /api/pdf/{file_id}
```

### Health Check
```
GET /api/health
```

## Response Example

```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "file_size_mb": 1.0,
  "metadata": {
    "page_count": 10,
    "document_category": "short-document"
  }
}
```

## Error Response

```json
{
  "error": "File validation failed",
  "detail": "File size exceeds 50MB limit"
}
```

## Examples

```bash
# Upload
curl -X POST http://localhost:8000/api/upload -F "file=@doc.pdf"

# Load URL
curl -X POST http://localhost:8000/api/load-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/doc.pdf"}'

# Get metadata
curl http://localhost:8000/api/metadata/{file_id}
```

## Status Codes
- 200: Success
- 400: Bad request (invalid file type, etc.)
- 404: Not found
- 413: File too large (>50MB)
- 422: Validation error
- 500: Server error

## Headers

All responses include:
- `X-Correlation-ID`: Request tracking ID
- `X-Request-ID`: Unique request identifier

## Type Safety

- Pydantic v2 models with validation
- Comprehensive error responses
- Python 3.9+ compatible types
- Runtime type checking