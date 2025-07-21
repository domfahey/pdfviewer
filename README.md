# PDF Viewer POC

Modern PDF viewer with React frontend and FastAPI backend.

## Quick Start

```bash
# Backend
uv pip install -e ".[dev]"
cd backend && uvicorn app.main:app --reload

# Frontend  
cd frontend && npm install && npm run dev
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Features

- PDF rendering with virtual scrolling
- Full-text search with highlighting
- Load PDFs from URLs
- Form field extraction
- Enhanced metadata and validation
- Material Design UI

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/upload` | Upload PDF (50MB limit) |
| `POST /api/load-url` | Load PDF from URL |
| `GET /api/pdf/{id}` | Download PDF |
| `GET /api/metadata/{id}` | Get metadata |
| `DELETE /api/pdf/{id}` | Delete PDF |

See [API Documentation](docs/API.md) for details.

## Documentation

- [API Reference](docs/API.md)
- [Technical Guide](docs/TECHNICAL.md)

## Limitations

- No authentication
- Single user
- Ephemeral storage
- No PDF editing

## Author

Created by Dominic Fahey (domfahey@gmail.com)

## License

MIT License - See [LICENSE](LICENSE) file for details
