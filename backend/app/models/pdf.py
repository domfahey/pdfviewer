"""Pydantic models for PDF file handling and metadata.

This module defines data models for PDF upload responses, metadata,
and file information using Pydantic v2.
"""

from datetime import UTC, datetime
import re
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_serializer,
    field_validator,
    model_validator,
)


def _validate_non_empty_string(value: str, field_name: str) -> None:
    """Helper to validate that a string is not empty or whitespace.
    
    Args:
        value: The string value to validate
        field_name: Name of the field being validated (for error messages)
        
    Raises:
        ValueError: If the string is empty or contains only whitespace
    """
    if not value or value.isspace():
        raise ValueError(f"{field_name} cannot be empty or whitespace")


class PDFMetadata(BaseModel):
    """PDF metadata model with enhanced validation for POC development."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "Sample PDF Document",
                "author": "John Doe",
                "page_count": 10,
                "file_size": 1024000,
                "encrypted": False,
            }
        },
    )

    title: Annotated[
        str | None, Field(None, max_length=500, description="PDF document title")
    ] = None
    author: Annotated[
        str | None, Field(None, max_length=200, description="PDF document author")
    ] = None
    subject: Annotated[
        str | None,
        Field(None, max_length=500, description="PDF document subject"),
    ] = None
    creator: Annotated[
        str | None,
        Field(None, max_length=200, description="PDF creation software"),
    ] = None
    producer: Annotated[
        str | None,
        Field(None, max_length=200, description="PDF producer software"),
    ] = None
    creation_date: Annotated[
        datetime | None, Field(None, description="PDF creation timestamp")
    ] = None
    modification_date: Annotated[
        datetime | None,
        Field(None, description="PDF last modification timestamp"),
    ] = None
    page_count: Annotated[
        int,
        Field(
            gt=0,
            le=10000,
            description="Number of pages in the PDF",
            json_schema_extra={"example": 10},
        ),
    ]
    file_size: Annotated[
        int,
        Field(
            gt=0,
            le=100_000_000,
            description="File size in bytes",
            json_schema_extra={"example": 1024000},
        ),
    ]
    encrypted: Annotated[
        bool,
        Field(
            description="Whether the PDF is password protected",
            json_schema_extra={"example": False},
        ),
    ] = False

    @field_validator("creation_date", "modification_date")
    @classmethod
    def validate_dates(cls, v: datetime | None) -> datetime | None:
        """Ensure dates are timezone-aware and not in the future."""
        if v is None:
            return v

        # Convert naive datetime to UTC
        if v.tzinfo is None:
            v = v.replace(tzinfo=UTC)

        # Ensure date is not in the future (with small tolerance for clock skew)
        now = datetime.now(UTC)
        if v > now:
            raise ValueError("PDF date cannot be in the future")

        return v

    @field_validator("title", "author", "subject", "creator", "producer")
    @classmethod
    def validate_text_fields(cls, v: str | None) -> str | None:
        """Validate and sanitize text metadata fields."""
        if v is None:
            return v

        # Strip whitespace (handled by ConfigDict, but explicit for clarity)
        v = v.strip()

        # Return None for empty strings
        if not v:
            return None

        # Check for potentially problematic characters for POC
        if any(char in v for char in ["\x00", "\x01", "\x02", "\x03"]):
            raise ValueError("Text contains invalid control characters")

        return v

    # page_count validation is already handled by Field constraints
    # (gt=0, le=10000)

    # file_size validation is already handled by Field constraints
    # (gt=0, le=100_000_000)

    @model_validator(mode="after")
    def validate_date_consistency(self) -> "PDFMetadata":
        """Ensure creation_date is before modification_date if both exist."""
        if (
            self.creation_date is not None
            and self.modification_date is not None
            and self.creation_date > self.modification_date
        ):
            raise ValueError("Creation date cannot be after modification date")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def file_size_mb(self) -> float:
        """File size in megabytes, rounded to 2 decimal places."""
        return round(self.file_size / (1024 * 1024), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_large_document(self) -> bool:
        """True if document has more than 100 pages."""
        return self.page_count > 100

    @field_serializer("creation_date", "modification_date")
    def serialize_dates(self, value: datetime | None) -> str | None:
        """Serialize dates to ISO format for POC consistency."""
        if value is None:
            return None
        # Ensure timezone-aware datetime is serialized consistently
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat()


class PDFUploadResponse(BaseModel):
    """PDF upload response model with enhanced validation."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "file_id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "document.pdf",
                "file_size": 1024000,
                "mime_type": "application/pdf",
                "upload_time": "2025-07-20T16:30:00Z",
            }
        },
    )

    file_id: Annotated[
        str,
        Field(
            min_length=36,
            max_length=36,
            pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            description="UUID v4 identifier for the uploaded file",
            json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
        ),
    ]
    filename: Annotated[
        str,
        Field(
            min_length=1,
            max_length=255,
            pattern=r'^[^<>:"/\\|?*]+\.pdf$',
            description="Original PDF filename with extension",
            json_schema_extra={"example": "document.pdf"},
        ),
    ]
    file_size: Annotated[
        int,
        Field(
            gt=0,
            le=100_000_000,
            description="File size in bytes (max 100MB for POC)",
            json_schema_extra={"example": 1024000},
        ),
    ]
    mime_type: Annotated[
        str,
        Field(
            pattern=r"^application/pdf$",
            description="MIME type - must be application/pdf",
            json_schema_extra={"example": "application/pdf"},
        ),
    ]
    upload_time: Annotated[
        datetime,
        Field(
            default_factory=lambda: datetime.now(UTC),
            description="UTC timestamp when file was uploaded",
        ),
    ]
    metadata: Annotated[
        PDFMetadata | None,
        Field(None, description="Extracted PDF metadata if available"),
    ] = None

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Enhanced filename validation with security and POC constraints."""
        # Basic requirements
        _validate_non_empty_string(v, "Filename")

        if not v.lower().endswith(".pdf"):
            raise ValueError("Filename must have .pdf extension")

        # Length validation
        if len(v) < 5:  # "a.pdf" minimum
            raise ValueError("Filename too short (minimum: a.pdf)")
        if len(v) > 255:
            raise ValueError("Filename too long (maximum: 255 characters)")

        # Security: Check for path traversal attempts
        if ".." in v or v.startswith("/") or v.startswith("\\"):
            raise ValueError("Filename contains path traversal sequences")

        # Check for potentially unsafe characters
        unsafe_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*", "\x00"]
        if any(char in v for char in unsafe_chars):
            raise ValueError(f"Filename contains unsafe characters: {unsafe_chars}")

        return v

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        """Enhanced MIME type validation for POC security."""
        _validate_non_empty_string(v, "MIME type")

        # Normalize the MIME type
        v = v.strip().lower()

        # Strict validation for POC - only accept exact match
        if v != "application/pdf":
            raise ValueError(
                f"Invalid MIME type '{v}'. Only 'application/pdf' is allowed in POC"
            )
        return "application/pdf"  # Return normalized version

    @field_validator("file_id")
    @classmethod
    def validate_file_id(cls, v: str) -> str:
        """Normalize UUID to lowercase for consistency."""
        return v.strip().lower()

    @model_validator(mode="after")
    def validate_upload_constraints(self) -> "PDFUploadResponse":
        """Ensure file size consistency between upload response and metadata."""
        if self.metadata and self.metadata.file_size != self.file_size:
            raise ValueError("File size mismatch between upload response and metadata")

        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def file_size_mb(self) -> float:
        """File size in megabytes for display purposes."""
        return round(self.file_size / (1024 * 1024), 2)

    @field_serializer("upload_time")
    def serialize_upload_time(self, value: datetime) -> str:
        """Serialize upload time to ISO format."""
        # Ensure timezone-aware datetime
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat()


class PDFInfo(BaseModel):
    """Complete PDF information model for internal use with enhanced serialization."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        # POC optimization: Removed ser_json_bytes due to compatibility
    )

    file_id: Annotated[
        str,
        Field(
            pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            description="UUID v4 identifier",
        ),
    ]
    filename: Annotated[
        str, Field(min_length=1, max_length=255, description="Original filename")
    ]
    file_size: Annotated[int, Field(gt=0, description="File size in bytes")]
    mime_type: Annotated[
        str, Field(pattern=r"^application/pdf$", description="MIME type")
    ]
    upload_time: Annotated[datetime, Field(description="Upload timestamp")]
    metadata: Annotated[PDFMetadata, Field(description="Complete PDF metadata")]

    @field_serializer("upload_time")
    def serialize_upload_time(self, value: datetime) -> str:
        """Serialize upload time consistently."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat()


class ErrorResponse(BaseModel):
    """Standardized error response model for API endpoints."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "error": "File validation failed",
                "detail": "File size exceeds maximum limit of 50MB",
                "error_code": "FILE_SIZE_EXCEEDED",
            }
        },
    )

    error: Annotated[
        str,
        Field(
            min_length=1,
            max_length=200,
            description="Brief error message",
            json_schema_extra={"example": "File validation failed"},
        ),
    ]
    detail: Annotated[
        str | None,
        Field(
            None,
            max_length=1000,
            description="Detailed error information",
            json_schema_extra={"example": "File size exceeds maximum limit of 50MB"},
        ),
    ] = None
    error_code: Annotated[
        str | None,
        Field(
            None,
            pattern=r"^[A-Z_]+$",
            max_length=50,
            description="Machine-readable error code",
            json_schema_extra={"example": "FILE_SIZE_EXCEEDED"},
        ),
    ] = None

    @field_validator("error")
    @classmethod
    def validate_error_message(cls, v: str) -> str:
        """Enhanced error message validation."""
        _validate_non_empty_string(v, "Error message")

        # Remove extra whitespace but preserve single spaces
        v = " ".join(v.split())

        # Ensure it doesn't contain sensitive information patterns
        sensitive_patterns = ["password", "token", "secret", "key=", "auth="]
        v_lower = v.lower()
        if any(pattern in v_lower for pattern in sensitive_patterns):
            raise ValueError("Error message may contain sensitive information")

        return v

    @field_validator("error_code")
    @classmethod
    def validate_error_code(cls, v: str | None) -> str | None:
        """Validate error code format (uppercase letters and underscores only)."""
        if v is None:
            return v

        # Remove whitespace and convert to uppercase
        v = v.strip().upper()
        if not v.replace("_", "").isalpha():
            raise ValueError("Error code must contain only letters and underscores")

        return v

    @model_validator(mode="after")
    def validate_error_consistency(self) -> "ErrorResponse":
        """Ensure error fields are consistent and appropriate for POC."""
        # If we have an error_code, we should have detail
        if self.error_code and not self.detail:
            raise ValueError(
                "Error code provided but detail is missing - required for POC debugging"
            )

        # Check that detail provides additional context beyond error
        if self.detail and self.detail.strip().lower() == self.error.strip().lower():
            raise ValueError(
                "Detail should provide additional context beyond the error message"
            )

        return self

    @field_serializer("error", "detail")
    def serialize_error_fields(self, value: str | None) -> str | None:
        """Serialize error fields with consistent formatting."""
        if value is None:
            return None
        # Ensure consistent formatting and remove extra whitespace
        return " ".join(value.split())
