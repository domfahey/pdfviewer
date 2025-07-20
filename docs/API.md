# API Documentation

This document provides comprehensive documentation for the PDF Viewer API endpoints.

## Base URL

- **Development**: `http://localhost:8000/api`
- **Production**: `https://your-domain.com/api`

## Authentication

Currently, the API does not require authentication. In production deployments, consider implementing:
- API key authentication
- JWT token validation  
- Rate limiting
- IP allowlisting

## Common Headers

### Request Headers
- `Content-Type`: `multipart/form-data` (for file uploads)
- `X-Correlation-ID`: Optional correlation ID for request tracing

### Response Headers
- `X-Correlation-ID`: Correlation ID for request tracing
- `Content-Type`: Varies by endpoint

## Error Handling

All endpoints return standardized error responses:

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad Request - Invalid input |
| `404` | Not Found - Resource doesn't exist |
| `413` | Payload Too Large - File size exceeds limit |
| `422` | Unprocessable Entity - Validation error |
| `500` | Internal Server Error |

## Endpoints

### Health Check

Check application health and status.

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-20T13:32:46.761046Z",
  "version": "0.1.0"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/health"
```

---

### Upload PDF

Upload a PDF file for processing and viewing.

```http
POST /api/upload
```

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field containing PDF file

**Validation Rules:**
- File must be PDF format (`.pdf` extension)
- Maximum file size: 50MB
- MIME type must be `application/pdf`

**Response:**
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "file_size": 1048576,
  "mime_type": "application/pdf",
  "metadata": {
    "title": "Sample Document",
    "author": "John Doe",
    "subject": "PDF Example",
    "creator": "Sample Creator",
    "producer": "Sample Producer",
    "creation_date": "2023-01-01T12:00:00Z",
    "modification_date": "2023-01-02T12:00:00Z",
    "page_count": 10,
    "file_size": 1048576,
    "encrypted": false
  }
}
```

**Error Responses:**

400 Bad Request:
```json
{
  "detail": "No filename provided"
}
```

413 Payload Too Large:
```json
{
  "detail": "File too large. Maximum size is 50.0MB"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@document.pdf"
```

**JavaScript Example:**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('/api/upload', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Upload result:', result);
```

---

### Retrieve PDF File

Get the actual PDF file content for viewing or downloading.

```http
GET /api/pdf/{file_id}
```

**Parameters:**
- `file_id` (path): UUID of the uploaded file

**Response:**
- Content-Type: `application/pdf`
- Body: PDF file binary content

**Error Responses:**

404 Not Found:
```json
{
  "detail": "File not found"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/pdf/550e8400-e29b-41d4-a716-446655440000" \
  --output document.pdf
```

**JavaScript Example:**
```javascript
const response = await fetch(`/api/pdf/${fileId}`);
if (response.ok) {
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  // Use URL for PDF.js or download
} else {
  console.error('File not found');
}
```

---

### Get PDF Metadata

Retrieve metadata information for a PDF file.

```http
GET /api/metadata/{file_id}
```

**Parameters:**
- `file_id` (path): UUID of the uploaded file

**Response:**
```json
{
  "title": "Sample Document",
  "author": "John Doe", 
  "subject": "PDF Example",
  "creator": "Sample Creator",
  "producer": "Sample Producer",
  "creation_date": "2023-01-01T12:00:00Z",
  "modification_date": "2023-01-02T12:00:00Z",
  "page_count": 10,
  "file_size": 1048576,
  "encrypted": false
}
```

**Metadata Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `title` | `string?` | Document title |
| `author` | `string?` | Document author |
| `subject` | `string?` | Document subject |
| `creator` | `string?` | Application that created the PDF |
| `producer` | `string?` | PDF producer software |
| `creation_date` | `string?` | ISO 8601 creation timestamp |
| `modification_date` | `string?` | ISO 8601 modification timestamp |
| `page_count` | `number` | Number of pages in the document |
| `file_size` | `number` | File size in bytes |
| `encrypted` | `boolean` | Whether the PDF is password-protected |

**Error Responses:**

404 Not Found:
```json
{
  "detail": "File not found"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/metadata/550e8400-e29b-41d4-a716-446655440000"
```

**JavaScript Example:**
```javascript
const response = await fetch(`/api/metadata/${fileId}`);
const metadata = await response.json();
console.log(`Document has ${metadata.page_count} pages`);
```

---

### Delete PDF File

Remove a PDF file from the server.

```http
DELETE /api/pdf/{file_id}
```

**Parameters:**
- `file_id` (path): UUID of the uploaded file

**Response:**
```json
{
  "success": true
}
```

**Error Responses:**

404 Not Found:
```json
{
  "detail": "File not found"
}
```

500 Internal Server Error:
```json
{
  "detail": "Failed to delete file: [error details]"
}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/pdf/550e8400-e29b-41d4-a716-446655440000"
```

**JavaScript Example:**
```javascript
const response = await fetch(`/api/pdf/${fileId}`, {
  method: 'DELETE'
});

if (response.ok) {
  const result = await response.json();
  console.log('File deleted successfully');
} else {
  console.error('Failed to delete file');
}
```

## Data Models

### PDFUploadResponse

Complete response from successful file upload.

```typescript
interface PDFUploadResponse {
  file_id: string;           // UUID identifier
  filename: string;          // Original filename
  file_size: number;         // Size in bytes
  mime_type: string;         // MIME type (application/pdf)
  metadata: PDFMetadata;     // Extracted metadata
}
```

### PDFMetadata

PDF document metadata extracted during upload.

```typescript
interface PDFMetadata {
  title?: string;            // Document title
  author?: string;           // Document author
  subject?: string;          // Document subject
  creator?: string;          // Creating application
  producer?: string;         // PDF producer
  creation_date?: string;    // ISO 8601 timestamp
  modification_date?: string; // ISO 8601 timestamp
  page_count: number;        // Number of pages
  file_size: number;         // File size in bytes
  encrypted: boolean;        // Password protection status
}
```

## Rate Limiting

Consider implementing rate limiting for production:

```
- Upload endpoint: 10 requests per minute per IP
- Retrieval endpoints: 100 requests per minute per IP
- Delete endpoint: 5 requests per minute per IP
```

## Logging and Monitoring

All API requests are logged with:
- Request correlation IDs
- Performance timing
- Request/response details
- Error context

Example log entry:
```json
{
  "timestamp": "2025-07-20T13:32:47.123456Z",
  "level": "info", 
  "logger": "app.middleware.logging",
  "message": "Request completed",
  "method": "POST",
  "url": "/api/upload",
  "status_code": 200,
  "duration_ms": 145.23,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## SDK Examples

### Python SDK Example

```python
import requests
from pathlib import Path

class PDFViewerClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
    def upload_pdf(self, file_path: Path) -> dict:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/pdf')}
            response = requests.post(f'{self.base_url}/api/upload', files=files)
            response.raise_for_status()
            return response.json()
    
    def get_metadata(self, file_id: str) -> dict:
        response = requests.get(f'{self.base_url}/api/metadata/{file_id}')
        response.raise_for_status()
        return response.json()
    
    def download_pdf(self, file_id: str, output_path: Path):
        response = requests.get(f'{self.base_url}/api/pdf/{file_id}')
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
    
    def delete_pdf(self, file_id: str) -> bool:
        response = requests.delete(f'{self.base_url}/api/pdf/{file_id}')
        response.raise_for_status()
        return response.json()['success']

# Usage
client = PDFViewerClient('http://localhost:8000')
result = client.upload_pdf(Path('document.pdf'))
print(f"Uploaded file: {result['file_id']}")
```

### JavaScript/TypeScript SDK Example

```typescript
class PDFViewerClient {
  constructor(private baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  async uploadPDF(file: File): Promise<PDFUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${this.baseUrl}/api/upload`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getMetadata(fileId: string): Promise<PDFMetadata> {
    const response = await fetch(`${this.baseUrl}/api/metadata/${fileId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to get metadata: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getPDFBlob(fileId: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/pdf/${fileId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to get PDF: ${response.statusText}`);
    }
    
    return response.blob();
  }

  async deletePDF(fileId: string): Promise<boolean> {
    const response = await fetch(`${this.baseUrl}/api/pdf/${fileId}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) {
      throw new Error(`Failed to delete PDF: ${response.statusText}`);
    }
    
    const result = await response.json();
    return result.success;
  }
}

// Usage
const client = new PDFViewerClient('http://localhost:8000');
const result = await client.uploadPDF(file);
console.log(`Uploaded file: ${result.file_id}`);
```

## OpenAPI Schema

The API automatically generates OpenAPI/Swagger documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Testing

### API Testing with curl

```bash
# Test health endpoint
curl -v http://localhost:8000/api/health

# Upload a PDF
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test.pdf" \
  -H "X-Correlation-ID: test-123"

# Get metadata
curl http://localhost:8000/api/metadata/YOUR_FILE_ID

# Download PDF
curl http://localhost:8000/api/pdf/YOUR_FILE_ID -o downloaded.pdf

# Delete PDF
curl -X DELETE http://localhost:8000/api/pdf/YOUR_FILE_ID
```

### API Testing with Python

```python
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_upload_pdf():
    with open("test.pdf", "rb") as f:
        response = client.post("/api/upload", files={"file": f})
    
    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data
    assert data["mime_type"] == "application/pdf"

def test_get_metadata():
    # First upload a file
    with open("test.pdf", "rb") as f:
        upload_response = client.post("/api/upload", files={"file": f})
    
    file_id = upload_response.json()["file_id"]
    
    # Get metadata
    response = client.get(f"/api/metadata/{file_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "page_count" in data
    assert "file_size" in data
```

## Security Considerations

### File Validation
- MIME type verification beyond file extension
- File size limits to prevent DoS attacks
- Virus scanning (recommended for production)
- Content validation to ensure valid PDF structure

### Input Sanitization
- UUID validation for file IDs
- Filename sanitization for storage
- Path traversal prevention
- SQL injection prevention (if using database)

### Production Hardening
- HTTPS enforcement
- CORS configuration
- Rate limiting
- Input validation
- Error message sanitization
- Log data sanitization