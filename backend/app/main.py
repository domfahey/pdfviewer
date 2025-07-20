import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import health, pdf, upload
from .services.pdf_service import PDFService

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Global PDF service instance
pdf_service = PDFService()

app = FastAPI(
    title="PDF Viewer API",
    description="Backend API for PDF viewer POC",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize shared service in routers
upload.init_pdf_service(pdf_service)
pdf.init_pdf_service(pdf_service)

# Include API routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(pdf.router, prefix="/api", tags=["pdf"])

# Serve uploaded files (for development only)
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "PDF Viewer API is running"}
