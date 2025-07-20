# PDF Viewer POC

A modern PDF viewer proof of concept with React 18+ frontend and FastAPI backend.

## Features

- PDF upload and viewing with PDF.js
- Virtual page rendering for performance
- Annotation support (viewing and interaction)
- Search functionality
- Thumbnail navigation
- Print and download capabilities

## Architecture

- **Frontend**: React 18 + TypeScript + Vite + PDF.js
- **Backend**: FastAPI + Python 3.9+ + UV

## Development

### Backend Setup

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Run development server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `POST /api/upload` - Upload PDF file
- `GET /api/pdf/{file_id}` - Retrieve PDF file
- `GET /api/metadata/{file_id}` - Get PDF metadata
- `DELETE /api/pdf/{file_id}` - Delete PDF file
- `GET /api/health` - Health check

## Testing

```bash
# Backend tests
pytest

# Frontend tests
npm test
```