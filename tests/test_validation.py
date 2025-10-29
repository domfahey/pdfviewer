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

    def test_validate_file_id_empty_string(self):
        """Test validation rejects empty string."""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_id("")

        assert exc_info.value.status_code == 400
        assert "File ID is required" in exc_info.value.detail

    def test_validate_file_id_whitespace_only(self):
        """Test validation rejects whitespace-only string."""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_id("   ")

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

    def test_validate_required_string_empty(self):
        """Test validation rejects empty string."""
        with pytest.raises(HTTPException) as exc_info:
            validate_required_string("", "username")

        assert exc_info.value.status_code == 400
        assert "username is required" in exc_info.value.detail

    def test_validate_required_string_none(self):
        """Test validation rejects None."""
        with pytest.raises(HTTPException) as exc_info:
            validate_required_string(None, "email")

        assert exc_info.value.status_code == 400
        assert "email is required" in exc_info.value.detail

    def test_validate_required_string_whitespace_only(self):
        """Test validation rejects whitespace-only string."""
        with pytest.raises(HTTPException) as exc_info:
            validate_required_string("   ", "password")

        assert exc_info.value.status_code == 400
        assert "password is required" in exc_info.value.detail

    def test_validate_required_string_with_logger(self):
        """Test validation logs error when logger provided."""
        mock_logger = Mock(spec=APILogger)

        with pytest.raises(HTTPException):
            validate_required_string("", "test_field", mock_logger)

        # Verify logger was called with field name
        mock_logger.log_validation_error.assert_called_once()
        call_args = mock_logger.log_validation_error.call_args
        assert "Empty test_field provided" in call_args[0]
