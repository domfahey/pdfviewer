import os
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "0.1.0"
    uptime: str = "N/A"
    storage_available: bool


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    # Check if upload directory is accessible
    upload_dir = "uploads"
    storage_available = True
    try:
        os.makedirs(upload_dir, exist_ok=True)
        # Try to write a test file
        test_file = os.path.join(upload_dir, ".health_check")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
    except Exception:
        storage_available = False

    return HealthResponse(
        status="healthy" if storage_available else "degraded",
        timestamp=datetime.now(timezone.utc),
        storage_available=storage_available,
    )
