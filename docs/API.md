# API Reference

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.5+-blue.svg)](https://docs.pydantic.dev/)

Base URL: `http://localhost:8000/api`

## Table of Contents

- [Interactive Documentation](#interactive-documentation)
- [Endpoints](#endpoints)
  - [Upload PDF](#upload-pdf)
  - [Load from URL](#load-from-url)
  - [Get PDF](#get-pdf)
  - [Get Metadata](#get-metadata)
  - [Delete PDF](#delete-pdf)
  - [Health Check](#health-check)
- [Response Example](#response-example)
- [Error Response](#error-response)
- [Examples](#examples)
- [Status Codes](#status-codes)
- [Headers](#headers)
- [Type Safety](#type-safety)

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
    "document_category": "short-document",
    "complexity_score": 3.5,
    "has_forms": false,
    "has_images": true
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

### Upload a PDF File
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf"
```

### Load PDF from URL
```bash
curl -X POST http://localhost:8000/api/load-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/document.pdf"}'
```

### Get PDF Metadata
```bash
curl http://localhost:8000/api/metadata/{file_id}
```

### Download PDF
```bash
curl -O http://localhost:8000/api/pdf/{file_id}
```

### Delete PDF
```bash
curl -X DELETE http://localhost:8000/api/pdf/{file_id}
```

## Status Codes

| Code | Description |
|------|-------------|
| `200` | ✅ Success |
| `400` | ❌ Bad request (invalid file type, etc.) |
| `404` | 🔍 Not found |
| `413` | 📦 File too large (>50MB) |
| `422` | ⚠️ Validation error |
| `500` | 🔥 Server error |

## Headers

All responses include:
- `X-Correlation-ID`: Request tracking ID
- `X-Request-ID`: Unique request identifier

## Type Safety

- Pydantic v2 models with validation
- Comprehensive error responses
- Python 3.11+ with modern type annotations
- Runtime type checking