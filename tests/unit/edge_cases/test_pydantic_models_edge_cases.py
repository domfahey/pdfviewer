"""Edge case tests for Pydantic models.

This module contains edge case tests for Pydantic models including:
- Field validation boundary conditions
- Invalid values (zero, negative, out of range)
- Type validation edge cases
"""

import pytest
from pydantic import ValidationError

from backend.app.models.pdf import PDFMetadata


class TestPDFMetadataEdgeCases:
    """Test PDFMetadata model edge cases."""

    def test_field_validation_page_count_invalid(self):
        """Test page_count validation edge cases."""
        # Invalid cases - should raise ValidationError
        with pytest.raises(ValidationError):
            PDFMetadata(page_count=0, file_size=1024)

        with pytest.raises(ValidationError):
            PDFMetadata(page_count=-1, file_size=1024)

        with pytest.raises(ValidationError):
            PDFMetadata(page_count=10001, file_size=1024)

    def test_field_validation_file_size_invalid(self):
        """Test file_size validation edge cases."""
        # Invalid cases - should raise ValidationError
        with pytest.raises(ValidationError):
            PDFMetadata(page_count=1, file_size=0)

        with pytest.raises(ValidationError):
            PDFMetadata(page_count=1, file_size=-1)

        with pytest.raises(ValidationError):
            PDFMetadata(page_count=1, file_size=100_000_001)  # > 100MB

    def test_field_validation_page_count_boundary(self):
        """Test page_count boundary values."""
        # Minimum valid value
        metadata_min = PDFMetadata(page_count=1, file_size=1024)
        assert metadata_min.page_count == 1

        # Maximum valid value
        metadata_max = PDFMetadata(page_count=10000, file_size=1024)
        assert metadata_max.page_count == 10000

    def test_field_validation_file_size_boundary(self):
        """Test file_size boundary values."""
        # Minimum valid value
        metadata_min = PDFMetadata(page_count=1, file_size=1)
        assert metadata_min.file_size == 1

        # Maximum valid value (100MB)
        metadata_max = PDFMetadata(page_count=1, file_size=100_000_000)
        assert metadata_max.file_size == 100_000_000
