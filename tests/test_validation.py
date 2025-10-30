"""Tests for validation utilities."""

import pytest
from unittest.mock import Mock

from fastapi import HTTPException

from backend.app.utils.validation import validate_file_id, validate_required_string
from backend.app.utils.api_logging import APILogger


class TestValidateFileId:
    """Test file ID validation."""

    def test_validate_file_id_valid(self):
        """Test validation with valid file ID."""
        result = validate_file_id("test-123")
        assert result == "test-123"

    def test_validate_file_id_with_whitespace(self):
        """Test validation strips whitespace."""
        result = validate_file_id("  test-123  ")
        assert result == "test-123"

    @pytest.mark.parametrize(
        "file_id",
        ["", "   "],
        ids=["empty_string", "whitespace_only"],
    )
    def test_validate_file_id_invalid(self, file_id):
        """Test validation rejects empty or whitespace-only strings."""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_id(file_id)

        assert exc_info.value.status_code == 400
        assert "File ID is required" in exc_info.value.detail

    def test_validate_file_id_with_logger(self):
        """Test validation logs error when logger provided."""
        mock_logger = Mock(spec=APILogger)

        with pytest.raises(HTTPException):
            validate_file_id("", mock_logger)

        # Verify logger was called
        mock_logger.log_validation_error.assert_called_once_with(
            "Empty file_id provided"
        )

    def test_validate_file_id_without_logger(self):
        """Test validation works without logger."""
        # Should not raise any AttributeError
        with pytest.raises(HTTPException) as exc_info:
            validate_file_id("", None)

        assert exc_info.value.status_code == 400


class TestValidateRequiredString:
    """Test required string validation."""

    def test_validate_required_string_valid(self):
        """Test validation with valid string."""
        result = validate_required_string("test-value", "field_name")
        assert result == "test-value"

    def test_validate_required_string_with_whitespace(self):
        """Test validation strips whitespace."""
        result = validate_required_string("  test-value  ", "field_name")
        assert result == "test-value"

    @pytest.mark.parametrize(
        "value,field_name",
        [
            ("", "username"),
            (None, "email"),
            ("   ", "password"),
        ],
        ids=["empty_string", "none_value", "whitespace_only"],
    )
    def test_validate_required_string_invalid(self, value, field_name):
        """Test validation rejects empty, None, or whitespace-only strings."""
        with pytest.raises(HTTPException) as exc_info:
            validate_required_string(value, field_name)

        assert exc_info.value.status_code == 400
        assert f"{field_name} is required" in exc_info.value.detail

    def test_validate_required_string_with_logger(self):
        """Test validation logs error when logger provided."""
        mock_logger = Mock(spec=APILogger)

        with pytest.raises(HTTPException):
            validate_required_string("", "test_field", mock_logger)

        # Verify logger was called with expected message
        mock_logger.log_validation_error.assert_called_once()
        call_args = mock_logger.log_validation_error.call_args
        # Check the first positional argument contains the expected message
        assert "Empty test_field provided" in call_args.args[0]


class TestApiEndpointHandler:
    """Test api_endpoint_handler context manager."""

    def test_api_endpoint_handler_success(self):
        """Test context manager with successful operation."""
        from backend.app.utils.validation import api_endpoint_handler

        result = None
        with api_endpoint_handler("test_operation", file_id="test-123") as logger:
            result = "success"
            assert logger.operation == "test_operation"
            logger.log_processing_success(file_id="test-123", result=result)

        assert result == "success"

    def test_api_endpoint_handler_with_http_exception(self):
        """Test context manager propagates HTTPException."""
        from backend.app.utils.validation import api_endpoint_handler

        with pytest.raises(HTTPException) as exc_info:
            with api_endpoint_handler("test_operation", file_id="test-123"):
                raise HTTPException(status_code=404, detail="Not found")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Not found"

    def test_api_endpoint_handler_with_generic_exception(self):
        """Test context manager converts generic exceptions to HTTPException."""
        from backend.app.utils.validation import api_endpoint_handler

        with pytest.raises(HTTPException) as exc_info:
            with api_endpoint_handler(
                "test_operation",
                file_id="test-123",
                default_error_message="Operation failed"
            ):
                raise ValueError("Something went wrong")

        assert exc_info.value.status_code == 500
        assert "Operation failed" in exc_info.value.detail
        assert "Something went wrong" in exc_info.value.detail

    def test_api_endpoint_handler_validates_file_id(self):
        """Test context manager validates file_id if provided."""
        from backend.app.utils.validation import api_endpoint_handler

        # Empty file_id should raise validation error
        with pytest.raises(HTTPException) as exc_info:
            with api_endpoint_handler("test_operation", file_id=""):
                pass

        assert exc_info.value.status_code == 400
        assert "File ID is required" in exc_info.value.detail

    def test_api_endpoint_handler_without_file_id(self):
        """Test context manager works without file_id validation."""
        from backend.app.utils.validation import api_endpoint_handler

        result = None
        with api_endpoint_handler("test_operation") as logger:
            result = "success"
            assert logger.operation == "test_operation"

        assert result == "success"
