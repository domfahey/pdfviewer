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

- **PDF Rendering**: High-performance viewer with React 18 compatibility
- **Enhanced Upload**: 50MB limit with Pydantic v2 validation
- **Smart Metadata**: Extraction with complexity scoring and categorization  
- **Comprehensive Logging**: Correlation IDs, performance metrics, debug mode
- **Type Safety**: Full TypeScript coverage with zero linting errors
- **CORS Support**: Multi-port development environment support
- **OpenAPI Documentation**: Auto-generated with enhanced response models

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
pytest              # Backend (0 tests)
npm test           # Frontend (39 tests passing)

# Code quality (zero errors/warnings)
ruff check . && ruff format .  # Python
npm run lint && npm run format # TypeScript
mypy . && npx tsc --noEmit     # Type checking
```

## Documentation

- [API Reference](docs/API.md) - Enhanced endpoints with Pydantic v2 validation
- [Technical Guide](docs/TECHNICAL.md) - Setup, deployment, logging, and CORS configuration

## Limitations

- No authentication
- Single user
- Ephemeral storage
- No PDF editing

## Author

Created by Dominic Fahey (domfahey@gmail.com)

## License

MIT License - See [LICENSE](LICENSE) file for details