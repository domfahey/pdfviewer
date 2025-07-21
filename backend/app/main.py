import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import health, pdf, upload
from .core.logging import configure_logging, get_logger
from .middleware.logging import LoggingMiddleware
from .services.pdf_service import PDFService

# Configure logging first thing - default to DEBUG for development
configure_logging(
    level=os.getenv("LOG_LEVEL", "DEBUG"),  # Debug mode by default
    json_logs=os.getenv("JSON_LOGS", "false").lower() == "true",
    enable_correlation_id=True,
)

logger = get_logger(__name__)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
logger.info("Upload directory initialized", upload_dir=str(UPLOAD_DIR))

# Global PDF service instance
pdf_service = PDFService()
logger.info("PDF service initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info(
        "PDF Viewer API starting up",
        version="0.1.0",
        upload_dir=str(UPLOAD_DIR),
        environment=os.getenv("ENVIRONMENT", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
    yield
    # Shutdown
    logger.info("PDF Viewer API shutting down")


app = FastAPI(
    title="PDF Viewer API",
    description="Backend API for PDF viewer POC",
    version="0.1.0",
    lifespan=lifespan,
)

# Add logging middleware first (before CORS)
app.add_middleware(LoggingMiddleware)
logger.info("Logging middleware configured")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware configured")

# Initialize shared service in routers
upload.init_pdf_service(pdf_service)
pdf.init_pdf_service(pdf_service)

# Include API routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(pdf.router, prefix="/api", tags=["pdf"])
logger.info("API routers configured")

# Serve uploaded files (for development only)
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    logger.info("Static file serving configured for uploads directory")


@app.get("/")
async def root() -> dict[str, str]:
    logger.info("Root endpoint accessed")
    return {"message": "PDF Viewer API is running"}
