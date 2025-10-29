import os
import re
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from ..utils.api_logging import APILogger, log_api_call

router = APIRouter()

# Compile regex pattern once for performance
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*)?$")


class HealthResponse(BaseModel):
    """Health check response with enhanced validation for POC monitoring."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2025-07-20T16:30:00Z",
                "version": "0.1.0",
                "uptime": "N/A",
                "storage_available": True,
            }
        },
    )

    status: Annotated[
        str,
        Field(
            pattern=r"^(healthy|degraded|unhealthy)$",
            description="Overall system health status",
            json_schema_extra={"example": "healthy"},
        ),
    ]
    timestamp: Annotated[
        datetime,
        Field(
            description="Current UTC timestamp",
            json_schema_extra={"example": "2025-07-20T16:30:00Z"},
        ),
    ]
    version: Annotated[
        str,
        Field(
            pattern=r"^\d+\.\d+\.\d+$",
            description="API version",
            json_schema_extra={"example": "0.1.0"},
        ),
    ] = "0.1.0"
    uptime: Annotated[
        str,
        Field(
            description="System uptime information",
            json_schema_extra={"example": "N/A"},
        ),
    ] = "N/A"
    storage_available: Annotated[
        bool,
        Field(
            description="Whether file storage is accessible",
            json_schema_extra={"example": True},
        ),
    ]

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Enhanced status validation with POC constraints."""
        if not v or v.isspace():
            raise ValueError("Status cannot be empty")

        # Normalize to lowercase
        v = v.strip().lower()

        # Validate against allowed values
        allowed_statuses = {"healthy", "degraded", "unhealthy"}
        if v not in allowed_statuses:
            raise ValueError(
                f"Status must be one of: {', '.join(sorted(allowed_statuses))}"
            )

        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Enhanced version validation for POC standards."""
        if not v or v.isspace():
            raise ValueError("Version cannot be empty")

        v = v.strip()

        # Semantic versioning pattern validation
        if not SEMVER_PATTERN.match(v):
            raise ValueError(
                "Version must follow semantic versioning (e.g., '1.0.0' or '1.0.0-beta')"
            )

        return v

    @field_validator("uptime")
    @classmethod
    def validate_uptime(cls, v: str) -> str:
        """Validate uptime string format for consistency."""
        if not v or v.isspace():
            return "N/A"  # Default for POC

        v = v.strip()

        # For POC, allow "N/A" or simple duration formats
        if v.upper() == "N/A":
            return "N/A"

        # Optional: Validate duration format (e.g., "2h 30m", "1d 5h")
        # For POC, we'll be lenient and accept any non-empty string
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_healthy(self) -> bool:
        """True if status is 'healthy'."""
        return self.status == "healthy"


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

    # Enhanced health status determination for POC
    if storage_available:
        health_status = "healthy"
    else:
        # For POC, storage issues are degraded, not unhealthy
        health_status = "degraded"
    # Create response with enhanced validation
    try:
        response = HealthResponse(
            status=health_status,
            timestamp=datetime.now(UTC),
            storage_available=storage_available,
        )
    except Exception as e:
        # If response creation fails, log and return minimal response
        api_logger.log_processing_error(
            e, health_status=health_status, response_creation="failed"
        )
        # Fallback response
        response = HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(UTC),
            storage_available=False,
        )

    api_logger.log_response_prepared(
        health_status=health_status,
        storage_available=storage_available,
        storage_error=storage_error,
        response_type="HealthResponse",
    )

    return response
