"""Tests for validation utilities."""

import pytest
from fastapi import HTTPException

from backend.app.utils.validation import (
    handle_api_errors,
    validate_file_id,
    validate_required_string,
)


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




class TestHandleApiErrors:
    """Test the handle_api_errors context manager."""

    def test_handle_api_errors_success(self):
        """Test that successful operations pass through unchanged."""
        with handle_api_errors("test operation"):
            result = "success"

        assert result == "success"

    def test_handle_api_errors_reraises_http_exception(self):
        """Test that HTTPExceptions are re-raised as-is."""
        original_exception = HTTPException(status_code=404, detail="Not found")

        with pytest.raises(HTTPException) as exc_info:
            with handle_api_errors("test operation"):
                raise original_exception

        # Should be the exact same exception instance
        assert exc_info.value is original_exception
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Not found"

    def test_handle_api_errors_wraps_generic_exception(self):
        """Test that generic exceptions are wrapped in HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            with handle_api_errors("retrieve file"):
                raise ValueError("Something went wrong")

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve file" in exc_info.value.detail
        assert "Something went wrong" in exc_info.value.detail

    def test_handle_api_errors_custom_status_code(self):
        """Test that custom status codes are used for generic exceptions."""
        with pytest.raises(HTTPException) as exc_info:
            with handle_api_errors("validate input", status_code=400):
                raise ValueError("Invalid input")

        assert exc_info.value.status_code == 400
        assert "Failed to validate input" in exc_info.value.detail
        assert "Invalid input" in exc_info.value.detail

    def test_handle_api_errors_operation_name_in_message(self):
        """Test that operation name is included in error message."""
        operations = ["retrieve file", "delete file", "process PDF"]

        for operation in operations:
            with pytest.raises(HTTPException) as exc_info:
                with handle_api_errors(operation):
                    raise RuntimeError("Test error")

            assert f"Failed to {operation}" in exc_info.value.detail
