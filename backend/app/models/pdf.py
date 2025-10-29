"""Pydantic models for PDF file handling and metadata.

This module defines data models for PDF upload responses, metadata,
and file information using Pydantic v2.
"""

from datetime import UTC, datetime
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_serializer,
    field_validator,
    model_serializer,
    model_validator,
)


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

    @field_validator("page_count")
    @classmethod
    def validate_page_count(cls, v: int) -> int:
        """Enhanced page count validation for POC constraints."""
        if v <= 0:
            raise ValueError("Page count must be positive")
        if v > 10000:
            raise ValueError("Page count exceeds POC limit of 10,000 pages")
        return v

    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """Enhanced file size validation with POC-specific constraints."""
        if v <= 0:
            raise ValueError("File size must be positive")
        if v > 100_000_000:  # 100MB POC limit
            raise ValueError("File size exceeds POC limit of 100MB")
        # Warn about very small files that might be corrupted
        if v < 1024:  # Less than 1KB
            # Note: We don't raise an error here, just validate it's positive
            pass
        return v

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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def document_complexity_score(self) -> float:
        """Calculate document complexity score for POC monitoring (0-100)."""
        score = 0.0

        # Page count factor (0-40 points)
        if self.page_count <= 10:
            score += 5
        elif self.page_count <= 50:
            score += 15
        elif self.page_count <= 200:
            score += 30
        else:
            score += 40

        # File size factor (0-30 points)
        size_mb = self.file_size_mb
        if size_mb <= 1:
            score += 5
        elif size_mb <= 10:
            score += 15
        elif size_mb <= 50:
            score += 25
        else:
            score += 30

        # Encryption factor (0-20 points)
        if self.encrypted:
            score += 20

        # Metadata richness factor (0-10 points)
        metadata_fields = [
            self.title,
            self.author,
            self.subject,
            self.creator,
            self.producer,
        ]
        filled_fields = sum(1 for field in metadata_fields if field)
        score += (filled_fields / len(metadata_fields)) * 10

        return round(min(score, 100.0), 1)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def document_category(self) -> str:
        """Categorize document for POC analysis."""
        if self.page_count == 1:
            return "single-page"
        elif self.page_count <= 10:
            return "short-document"
        elif self.page_count <= 50:
            return "medium-document"
        elif self.page_count <= 200:
            return "long-document"
        else:
            return "very-long-document"

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
        if not v or v.isspace():
            raise ValueError("Filename cannot be empty or whitespace")

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

        # POC-specific: Avoid names that might conflict with system files
        forbidden_names = ["con.pdf", "aux.pdf", "prn.pdf", "nul.pdf"]
        if v.lower() in forbidden_names:
            raise ValueError("Filename conflicts with system reserved names")

        return v

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        """Enhanced MIME type validation for POC security."""
        if not v or v.isspace():
            raise ValueError("MIME type cannot be empty")

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
        """Enhanced UUID validation with format checking."""
        if not v or v.isspace():
            raise ValueError("File ID cannot be empty")

        # Remove any whitespace
        v = v.strip()

        # UUID v4 format validation
        import re

        uuid_pattern = (
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        )
        if not re.match(uuid_pattern, v, re.IGNORECASE):
            raise ValueError("File ID must be a valid UUID v4 format")

        # Return lowercase for consistency
        return v.lower()

    @model_validator(mode="after")
    def validate_upload_constraints(self) -> "PDFUploadResponse":
        """POC-specific validation for upload constraints."""
        # Ensure file size and metadata are consistent if metadata exists
        if self.metadata and self.metadata.file_size != self.file_size:
            raise ValueError("File size mismatch between upload response and metadata")

        # POC constraint: Warn about large files that might cause performance issues
        large_file_threshold = 50_000_000  # 50MB
        if self.file_size > large_file_threshold:
            # In a real app, this might be logged as a warning
            # For POC, we allow it but could add monitoring
            pass

        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def file_size_mb(self) -> float:
        """File size in megabytes for display purposes."""
        return round(self.file_size / (1024 * 1024), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def upload_age_hours(self) -> float:
        """Hours since upload, useful for POC debugging."""
        now = datetime.now(UTC)
        # Ensure upload_time is timezone-aware
        upload_time = self.upload_time
        if upload_time.tzinfo is None:
            upload_time = upload_time.replace(tzinfo=UTC)

        delta = now - upload_time
        return round(delta.total_seconds() / 3600, 1)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def upload_status(self) -> str:
        """Status based on upload age for POC monitoring."""
        age_hours = self.upload_age_hours
        if age_hours < 1:
            return "fresh"
        elif age_hours < 24:
            return "recent"
        elif age_hours < 168:  # 1 week
            return "aging"
        else:
            return "old"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def processing_priority(self) -> str:
        """Suggested processing priority for POC workflows."""
        # Base priority on file size and complexity
        if self.file_size_mb > 50:  # Large files
            return "low"  # Process during off-peak
        elif self.file_size_mb > 10:  # Medium files
            if self.metadata and self.metadata.page_count > 100:
                return "low"  # Complex medium files
            return "normal"
        else:  # Small files
            return "high"  # Quick to process

    @field_serializer("upload_time")
    def serialize_upload_time(self, value: datetime) -> str:
        """Serialize upload time to ISO format."""
        # Ensure timezone-aware datetime
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat()

    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Serialize model for POC API responses with all fields.

        Returns:
            dict: Serialized model data including computed fields.

        """
        # Get the default serialized data
        data = {
            "file_id": self.file_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "file_size_mb": self.file_size_mb,  # Include computed field
            "mime_type": self.mime_type,
            "upload_time": self.serialize_upload_time(self.upload_time),
            "upload_age_hours": self.upload_age_hours,  # Include computed field
            "upload_status": self.upload_status,  # Include computed field
            "processing_priority": self.processing_priority,  # Include computed field
            "metadata": self.metadata.model_dump() if self.metadata else None,
        }

        # Add POC-specific metadata for debugging
        data["_poc_info"] = {
            "serialized_at": datetime.now(UTC).isoformat(),
            "model_version": "2.0",
            "enhanced_validation": True,
        }

        return data


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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def storage_efficiency(self) -> float:
        """Calculate storage efficiency score for POC monitoring."""
        if not self.metadata:
            return 0.0

        # Bytes per page ratio
        bytes_per_page = self.file_size / self.metadata.page_count

        # Efficiency score (lower bytes per page = higher efficiency)
        if bytes_per_page < 50_000:  # < 50KB per page = very efficient
            return 1.0
        elif bytes_per_page < 100_000:  # < 100KB per page = good
            return 0.8
        elif bytes_per_page < 200_000:  # < 200KB per page = average
            return 0.6
        elif bytes_per_page < 500_000:  # < 500KB per page = poor
            return 0.4
        else:  # > 500KB per page = very poor
            return 0.2

    @field_serializer("upload_time")
    def serialize_upload_time(self, value: datetime) -> str:
        """Serialize upload time consistently."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat()

    @model_serializer
    def serialize_for_internal_use(self) -> dict[str, Any]:
        """Serialize model optimized for internal API responses.

        Returns:
            dict: Lightweight serialized data for internal use.

        """
        return {
            "file_id": self.file_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "upload_time": self.serialize_upload_time(self.upload_time),
            "metadata": self.metadata.model_dump(),
            "storage_efficiency": self.storage_efficiency,  # Include computed field
            "_internal": {
                "model_type": "PDFInfo",
                "version": "2.0",
                "enhanced_features": True,
            },
        }


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
        if not v or v.isspace():
            raise ValueError("Error message cannot be empty")

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
        """Enhanced error code validation with POC standards."""
        if v is None:
            return v

        # Remove whitespace
        v = v.strip().upper()

        # Must be uppercase with underscores only
        if not v.replace("_", "").isalpha():
            raise ValueError("Error code must contain only letters and underscores")

        # POC standard: Should start with category prefix
        valid_prefixes = ["FILE_", "VALIDATION_", "API_", "AUTH_", "SYSTEM_"]
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            # For POC, we'll be lenient but could enforce this
            pass

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

    @model_serializer
    def serialize_error_response(self) -> dict[str, Any]:
        """Serialize error responses with POC debugging information.

        Returns:
            dict: Error response data with debugging context.

        """
        data: dict[str, Any] = {
            "error": self.serialize_error_fields(self.error),
            "detail": self.serialize_error_fields(self.detail),
            "error_code": self.error_code,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Add POC debugging information
        data["_debug"] = {
            "error_type": (
                "validation" if "validation" in self.error.lower() else "processing"
            ),
            "has_detail": self.detail is not None,
            "has_error_code": self.error_code is not None,
            "severity": (
                "high"
                if self.error_code and self.error_code.startswith("SYSTEM_")
                else "medium"
            ),
        }

        return data
