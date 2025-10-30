"""Tests for validation utilities."""

import pytest

from fastapi import HTTPException

from backend.app.utils.validation import validate_file_id, validate_required_string


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
        assert "password is required" in exc_info.value.detail
