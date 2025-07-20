import os
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from ..utils.api_logging import APILogger, log_api_call

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "0.1.0"
    uptime: str = "N/A"
    storage_available: bool


@router.get("/health", response_model=HealthResponse)
@log_api_call("health_check", log_params=False, log_response=True, log_timing=True)
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    api_logger = APILogger("health_check")

    api_logger.log_request_received()
    api_logger.log_processing_start(operation="system_health_check")

    # Check if upload directory is accessible
    upload_dir = "uploads"
    storage_available = True
    storage_error = None

    try:
        os.makedirs(upload_dir, exist_ok=True)
        # Try to write a test file
        test_file = os.path.join(upload_dir, ".health_check")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)

        api_logger.log_processing_success(
            upload_dir=upload_dir, storage_check="passed", storage_available=True
        )

    except Exception as e:
        storage_available = False
        storage_error = str(e)

        api_logger.log_processing_error(
            e, upload_dir=upload_dir, storage_check="failed", storage_available=False
        )

    health_status = "healthy" if storage_available else "degraded"
    response = HealthResponse(
        status=health_status,
        timestamp=datetime.now(timezone.utc),
        storage_available=storage_available,
    )

    api_logger.log_response_prepared(
        health_status=health_status,
        storage_available=storage_available,
        storage_error=storage_error,
        response_type="HealthResponse",
    )

    return response
