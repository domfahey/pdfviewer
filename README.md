# PDF Viewer POC

Modern PDF viewer proof of concept with React frontend and FastAPI backend.

## Quick Start

```bash
# Backend
uv pip install -e ".[dev]"
cd backend && uvicorn app.main:app --reload

# Frontend  
cd frontend && npm install && npm run dev

# Docker
docker-compose up -d
```

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## Features

- PDF rendering with virtual page loading
- File upload/download (50MB limit)
- Metadata extraction
- Structured logging with correlation IDs
- OpenAPI documentation

## API

| Endpoint | Description |
|----------|-------------|
| `POST /api/upload` | Upload PDF |
| `GET /api/pdf/{id}` | Download PDF |
| `GET /api/metadata/{id}` | Get metadata |
| `DELETE /api/pdf/{id}` | Delete PDF |
| `GET /api/health` | Health check |

Example:
```bash
curl -X POST http://localhost:8000/api/upload -F "file=@document.pdf"
```

## Project Structure

```
backend/
├── app/
│   ├── api/         # Endpoints
│   ├── models/      # Data models
│   ├── services/    # Business logic
│   └── utils/       # Logging
frontend/
└── src/
    ├── components/  # React components
    └── services/    # API client
```

## Development

```bash
# Tests
pytest              # Backend
npm test           # Frontend

# Code quality
ruff check . && black .
npm run lint
```

## Documentation

- [API Reference](docs/API.md) - Endpoint details
- [Technical Guide](docs/TECHNICAL.md) - Setup, deployment, logging

## Limitations

- No authentication
- Single user
- Ephemeral storage
- No PDF editing

## Author

Created by Dominic Fahey (domfahey@gmail.com)

## License

MIT License - See [LICENSE](LICENSE) file for details