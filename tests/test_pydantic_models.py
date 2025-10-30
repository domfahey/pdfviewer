"""
Comprehensive tests for Pydantic v2 models with enhanced validation.

Tests cover all model validation, computed fields, serialization,
and POC-specific enhancements in the PDF models.
"""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from backend.app.models.pdf import (
    ErrorResponse,
    PDFInfo,
    PDFMetadata,
    PDFUploadResponse,
    calculate_file_size_mb,
    serialize_datetime_to_iso,
)


class TestPDFMetadataModel:
    """Test PDFMetadata model with Pydantic v2 features."""

    def test_minimal_valid_metadata(self):
        """Test creating PDFMetadata with minimal required fields."""
        metadata = PDFMetadata(page_count=1, file_size=1024)

        assert metadata.page_count == 1
        assert metadata.file_size == 1024
        assert metadata.encrypted is False  # Default value
        assert metadata.title is None
        assert metadata.author is None

    def test_full_metadata_with_all_fields(self):
        """Test creating PDFMetadata with all fields populated."""
        creation_date = datetime.now(UTC) - timedelta(days=1)
        modification_date = datetime.now(UTC)

        metadata = PDFMetadata(
            title="Test Document",
            author="John Doe",
            subject="Test Subject",
            creator="Test Creator",
            producer="Test Producer",
            creation_date=creation_date,
            modification_date=modification_date,
            page_count=10,
            file_size=1024000,
            encrypted=True,
        )

        assert metadata.title == "Test Document"
        assert metadata.author == "John Doe"
        assert metadata.subject == "Test Subject"
        assert metadata.creator == "Test Creator"
        assert metadata.producer == "Test Producer"
        assert metadata.creation_date == creation_date
        assert metadata.modification_date == modification_date
        assert metadata.page_count == 10
        assert metadata.file_size == 1024000
        assert metadata.encrypted is True

    def test_computed_field_file_size_mb(self):
        """Test file_size_mb computed field."""
        metadata = PDFMetadata(
            page_count=1,
            file_size=1048576,  # 1MB
        )

        assert metadata.file_size_mb == 1.0

    def test_computed_field_is_large_document(self):
        """Test is_large_document computed field."""
        small_doc = PDFMetadata(page_count=50, file_size=1024)
        large_doc = PDFMetadata(page_count=150, file_size=1024)

        assert small_doc.is_large_document is False
        assert large_doc.is_large_document is True

    def test_field_validation_page_count(self):
        """Test page_count validation."""
        # Valid cases
        PDFMetadata(page_count=1, file_size=1024)
        PDFMetadata(page_count=100, file_size=1024)
        PDFMetadata(page_count=10000, file_size=1024)

        # Invalid cases
        with pytest.raises(ValidationError):
            PDFMetadata(page_count=0, file_size=1024)

        with pytest.raises(ValidationError):
            PDFMetadata(page_count=-1, file_size=1024)

        with pytest.raises(ValidationError):
            PDFMetadata(page_count=10001, file_size=1024)

    def test_field_validation_file_size(self):
        """Test file_size validation."""
        # Valid cases
        PDFMetadata(page_count=1, file_size=1)
        PDFMetadata(page_count=1, file_size=1024)
        PDFMetadata(page_count=1, file_size=100_000_000)  # 100MB

        # Invalid cases
        with pytest.raises(ValidationError):
            PDFMetadata(page_count=1, file_size=0)

        with pytest.raises(ValidationError):
            PDFMetadata(page_count=1, file_size=-1)

        with pytest.raises(ValidationError):
            PDFMetadata(page_count=1, file_size=100_000_001)  # > 100MB

    def test_field_validation_dates(self):
        """Test date field validation."""
        now = datetime.now(UTC)
        past_date = now - timedelta(days=1)
        future_date = now + timedelta(days=1)

        # Valid dates
        metadata = PDFMetadata(
            page_count=1, file_size=1024, creation_date=past_date, modification_date=now
        )
        assert metadata.creation_date == past_date
        assert metadata.modification_date == now

        # Invalid: future dates
        with pytest.raises(ValidationError):
            PDFMetadata(page_count=1, file_size=1024, creation_date=future_date)

    def test_field_validation_text_fields(self):
        """Test text field validation and sanitization."""
        # Valid text
        metadata = PDFMetadata(
            page_count=1,
            file_size=1024,
            title="  Valid Title  ",  # Should be stripped
            author="Valid Author",
        )
        assert metadata.title == "Valid Title"  # Whitespace stripped

        # Empty strings should become None
        metadata = PDFMetadata(
            page_count=1,
            file_size=1024,
            title="",
            author="   ",  # Only whitespace
        )
        assert metadata.title is None
        assert metadata.author is None

        # Invalid: control characters
        with pytest.raises(ValidationError):
            PDFMetadata(
                page_count=1, file_size=1024, title="Title\x00with control chars"
            )

    def test_model_validation_date_consistency(self):
        """Test model-level date consistency validation."""
        now = datetime.now(UTC)
        past_date = now - timedelta(days=1)

        # Valid: creation before modification
        PDFMetadata(
            page_count=1, file_size=1024, creation_date=past_date, modification_date=now
        )

        # Invalid: creation after modification
        with pytest.raises(ValidationError):
            PDFMetadata(
                page_count=1,
                file_size=1024,
                creation_date=now,
                modification_date=past_date,
            )

    def test_field_serialization_dates(self):
        """Test date field serialization."""
        now = datetime.now(UTC)

        metadata = PDFMetadata(page_count=1, file_size=1024, creation_date=now)

        serialized = metadata.model_dump()
        assert isinstance(serialized["creation_date"], str)
        # Should be ISO format with timezone (either Z or +00:00)
        assert serialized["creation_date"].endswith("Z") or serialized[
            "creation_date"
        ].endswith("+00:00")

    def test_string_whitespace_stripping(self):
        """Test that ConfigDict str_strip_whitespace works."""
        metadata = PDFMetadata(
            page_count=1,
            file_size=1024,
            title="  Title with spaces  ",
            author="  Author  ",
        )

        assert metadata.title == "Title with spaces"
        assert metadata.author == "Author"

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError):
            PDFMetadata(page_count=1, file_size=1024, extra_field="not allowed")


class TestPDFUploadResponseModel:
    """Test PDFUploadResponse model with enhanced validation."""

    def test_minimal_valid_response(self):
        """Test creating PDFUploadResponse with minimal fields."""
        upload_time = datetime.now(UTC)

        response = PDFUploadResponse(
            file_id="550e8400-e29b-41d4-a716-446655440000",
            filename="test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            upload_time=upload_time,
        )

        assert response.file_id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.filename == "test.pdf"
        assert response.file_size == 1024
        assert response.mime_type == "application/pdf"
        assert response.upload_time == upload_time
        assert response.metadata is None

    def test_computed_field_file_size_mb(self):
        """Test file_size_mb computed field."""
        response = PDFUploadResponse(
            file_id="550e8400-e29b-41d4-a716-446655440000",
            filename="test.pdf",
            file_size=2097152,  # 2MB
            mime_type="application/pdf",
        )

        assert response.file_size_mb == 2.0

    def test_field_validation_file_id(self):
        """Test file_id UUID validation."""
        # Valid UUID v4
        PDFUploadResponse(
            file_id="550e8400-e29b-41d4-a716-446655440000",
            filename="test.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )

        # Invalid UUID format
        with pytest.raises(ValidationError):
            PDFUploadResponse(
                file_id="invalid-uuid",
                filename="test.pdf",
                file_size=1024,
                mime_type="application/pdf",
            )

        # Invalid UUID version (v1 instead of v4)
        with pytest.raises(ValidationError):
            PDFUploadResponse(
                file_id="550e8400-e29b-11d4-a716-446655440000",  # v1 UUID
                filename="test.pdf",
                file_size=1024,
                mime_type="application/pdf",
            )

    def test_field_validation_filename(self):
        """Test filename validation with security checks."""
        # Valid filenames
        valid_filenames = ["test.pdf", "document-name.pdf", "my_file.pdf"]
        for filename in valid_filenames:
            PDFUploadResponse(
                file_id="550e8400-e29b-41d4-a716-446655440000",
                filename=filename,
                file_size=1024,
                mime_type="application/pdf",
            )

        # Invalid: no extension
        with pytest.raises(ValidationError):
            PDFUploadResponse(
                file_id="550e8400-e29b-41d4-a716-446655440000",
                filename="test",
                file_size=1024,
                mime_type="application/pdf",
            )

        # Invalid: wrong extension
        with pytest.raises(ValidationError):
            PDFUploadResponse(
                file_id="550e8400-e29b-41d4-a716-446655440000",
                filename="test.txt",
                file_size=1024,
                mime_type="application/pdf",
            )

        # Invalid: path traversal
        with pytest.raises(ValidationError):
            PDFUploadResponse(
                file_id="550e8400-e29b-41d4-a716-446655440000",
                filename="../test.pdf",
                file_size=1024,
                mime_type="application/pdf",
            )

        # Invalid: unsafe characters
        with pytest.raises(ValidationError):
            PDFUploadResponse(
                file_id="550e8400-e29b-41d4-a716-446655440000",
                filename="test<>.pdf",
                file_size=1024,
                mime_type="application/pdf",
            )

    def test_field_validation_mime_type(self):
        """Test MIME type validation."""
        # Valid MIME type
        PDFUploadResponse(
            file_id="550e8400-e29b-41d4-a716-446655440000",
            filename="test.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )

        # Invalid MIME type
        with pytest.raises(ValidationError):
            PDFUploadResponse(
                file_id="550e8400-e29b-41d4-a716-446655440000",
                filename="test.pdf",
                file_size=1024,
                mime_type="text/plain",
            )

    def test_model_validation_upload_constraints(self):
        """Test model-level upload constraints validation."""
        metadata = PDFMetadata(page_count=1, file_size=1024)

        # Valid: matching file sizes
        PDFUploadResponse(
            file_id="550e8400-e29b-41d4-a716-446655440000",
            filename="test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            metadata=metadata,
        )

        # Invalid: mismatched file sizes
        with pytest.raises(ValidationError):
            PDFUploadResponse(
                file_id="550e8400-e29b-41d4-a716-446655440000",
                filename="test.pdf",
                file_size=2048,  # Different from metadata
                mime_type="application/pdf",
                metadata=metadata,
            )

    def test_custom_model_serializer(self):
        """Test custom model serializer includes POC info."""
        response = PDFUploadResponse(
            file_id="550e8400-e29b-41d4-a716-446655440000",
            filename="test.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )

        serialized = response.serialize_model()

        # Check all expected fields are present
        assert "file_id" in serialized
        assert "filename" in serialized
        assert "file_size" in serialized
        assert "file_size_mb" in serialized
        assert "upload_age_hours" in serialized
        assert "upload_status" in serialized
        assert "processing_priority" in serialized

        # Check POC info
        assert "_poc_info" in serialized
        poc_info = serialized["_poc_info"]
        assert poc_info["model_version"] == "2.0"
        assert poc_info["enhanced_validation"] is True


class TestErrorResponseModel:
    """Test ErrorResponse model with enhanced validation."""

    def test_minimal_error_response(self):
        """Test creating ErrorResponse with minimal fields."""
        error = ErrorResponse(error="Test error")

        assert error.error == "Test error"
        assert error.detail is None
        assert error.error_code is None

    def test_full_error_response(self):
        """Test creating ErrorResponse with all fields."""
        error = ErrorResponse(
            error="File validation failed",
            detail="File size exceeds maximum limit",
            error_code="FILE_SIZE_EXCEEDED",
        )

        assert error.error == "File validation failed"
        assert error.detail == "File size exceeds maximum limit"
        assert error.error_code == "FILE_SIZE_EXCEEDED"

    def test_field_validation_error_message(self):
        """Test error message validation."""
        # Valid error message
        ErrorResponse(error="Valid error message")

        # Invalid: empty error
        with pytest.raises(ValidationError):
            ErrorResponse(error="")

        # Invalid: whitespace only
        with pytest.raises(ValidationError):
            ErrorResponse(error="   ")

        # Invalid: contains sensitive information
        with pytest.raises(ValidationError):
            ErrorResponse(error="Error with password: secret123")

    def test_field_validation_error_code(self):
        """Test error code validation."""
        # Valid error codes
        valid_codes = ["FILE_SIZE_EXCEEDED", "VALIDATION_ERROR", "API_ERROR"]
        for code in valid_codes:
            ErrorResponse(error="Test", detail="Test detail", error_code=code)

        # Invalid: lowercase
        with pytest.raises(ValidationError):
            ErrorResponse(
                error="Test", detail="Test detail", error_code="file_size_exceeded"
            )

        # Invalid: contains numbers
        with pytest.raises(ValidationError):
            ErrorResponse(error="Test", detail="Test detail", error_code="ERROR123")

    def test_model_validation_error_consistency(self):
        """Test model-level error consistency validation."""
        # Valid: error_code with detail
        ErrorResponse(
            error="Test error", detail="Detailed explanation", error_code="TEST_ERROR"
        )

        # Invalid: error_code without detail
        with pytest.raises(ValidationError):
            ErrorResponse(error="Test error", error_code="TEST_ERROR")

        # Invalid: detail same as error
        with pytest.raises(ValidationError):
            ErrorResponse(error="Test error", detail="Test error")

    def test_custom_model_serializer(self):
        """Test custom error serializer includes debug info."""
        error = ErrorResponse(
            error="File validation failed",
            detail="File size exceeds limit",
            error_code="FILE_SIZE_EXCEEDED",
        )

        serialized = error.serialize_error_response()

        # Check main fields
        assert serialized["error"] == "File validation failed"
        assert serialized["detail"] == "File size exceeds limit"
        assert serialized["error_code"] == "FILE_SIZE_EXCEEDED"
        assert "timestamp" in serialized

        # Check debug info
        assert "_debug" in serialized
        debug_info = serialized["_debug"]
        assert debug_info["has_detail"] is True
        assert debug_info["has_error_code"] is True
        assert debug_info["error_type"] in ["validation", "processing"]


class TestPDFInfoModel:
    """Test PDFInfo model for internal use."""

    def test_valid_pdf_info(self):
        """Test creating valid PDFInfo."""
        metadata = PDFMetadata(page_count=10, file_size=1024000)
        upload_time = datetime.now(UTC)

        pdf_info = PDFInfo(
            file_id="550e8400-e29b-41d4-a716-446655440000",
            filename="test.pdf",
            file_size=1024000,
            mime_type="application/pdf",
            upload_time=upload_time,
            metadata=metadata,
        )

        assert pdf_info.file_id == "550e8400-e29b-41d4-a716-446655440000"
        assert pdf_info.filename == "test.pdf"
        assert pdf_info.file_size == 1024000
        assert pdf_info.metadata == metadata


class TestHelperFunctions:
    """Test helper functions used in models."""

    def test_calculate_file_size_mb_small_file(self):
        """Test file size calculation for small file."""
        # 1 KB = 1024 bytes
        result = calculate_file_size_mb(1024)
        assert result == 0.0  # < 0.01 MB rounds to 0.0

    def test_calculate_file_size_mb_medium_file(self):
        """Test file size calculation for medium file."""
        # 1 MB = 1024 * 1024 bytes
        result = calculate_file_size_mb(1024 * 1024)
        assert result == 1.0

    def test_calculate_file_size_mb_large_file(self):
        """Test file size calculation for large file."""
        # 50 MB
        result = calculate_file_size_mb(50 * 1024 * 1024)
        assert result == 50.0

    def test_calculate_file_size_mb_decimal_precision(self):
        """Test that file size is rounded to 2 decimal places."""
        # 1.5 MB + small fraction
        result = calculate_file_size_mb(1_572_864)  # 1.5 MB
        assert result == 1.5

    def test_serialize_datetime_to_iso_with_utc(self):
        """Test datetime serialization with UTC timezone."""
        dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
        result = serialize_datetime_to_iso(dt)

        assert result is not None
        assert "2025-01-15" in result
        assert "10:30:00" in result
        assert "+" in result or "Z" in result  # Timezone indicator

    def test_serialize_datetime_to_iso_with_naive(self):
        """Test datetime serialization with naive datetime (no timezone)."""
        dt = datetime(2025, 1, 15, 10, 30, 0)
        result = serialize_datetime_to_iso(dt)

        # Should add UTC timezone and serialize
        assert result is not None
        assert "2025-01-15" in result
        assert "10:30:00" in result

    def test_serialize_datetime_to_iso_with_none(self):
        """Test datetime serialization with None."""
        result = serialize_datetime_to_iso(None)
        assert result is None

    def test_serialize_datetime_to_iso_format_consistency(self):
        """Test that serialized format is consistent across multiple calls."""
        dt1 = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
        dt2 = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)

        result1 = serialize_datetime_to_iso(dt1)
        result2 = serialize_datetime_to_iso(dt2)

        assert result1 == result2
