"""Edge case tests for validation utilities.

This module contains edge case tests for validation utilities including:
- Empty or whitespace-only strings
- None values
- Whitespace handling
"""

import pytest
from fastapi import HTTPException

from backend.app.utils.validation import (
    validate_file_id,
    validate_required_string,
)


class TestValidateFileIdEdgeCases:
    """Test file ID validation edge cases."""

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


class TestValidateRequiredStringEdgeCases:
    """Test required string validation edge cases."""

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
        assert "is required" in exc_info.value.detail
