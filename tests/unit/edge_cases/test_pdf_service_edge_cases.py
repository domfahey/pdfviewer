"""Edge case tests for PDF service validation.

This module contains edge case tests for the PDF service including:
- Missing or empty filenames
- Invalid file extensions
- Oversized files
- Case sensitivity in extensions
"""

from unittest.mock import Mock

import pytest
from fastapi import HTTPException, UploadFile

from backend.app.services.pdf_service import PDFService


@pytest.fixture
def pdf_service():
    """Create a temporary PDFService instance for testing."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as temp_dir:
        service = PDFService(upload_dir=temp_dir)
        yield service


class TestPDFServiceValidationEdgeCases:
    """Test file validation edge cases."""

    @pytest.mark.parametrize(
        "filename,expected_error",
        [
            (None, "filename"),
            ("", "filename"),
        ],
        ids=["no_filename", "empty_filename"],
    )
    def test_validate_file_missing_filename(
        self, pdf_service, filename, expected_error
    ):
        """Test validation fails when filename is missing or empty."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = filename
        mock_file.content_type = "application/pdf"
        mock_file.size = 1000

        with pytest.raises(HTTPException) as exc_info:
            pdf_service._validate_file(mock_file)

        assert exc_info.value.status_code == 400
        assert expected_error in exc_info.value.detail.lower()

    def test_validate_file_invalid_extension(self, pdf_service):
        """Test validation fails for non-PDF file extensions."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.size = 1000

        with pytest.raises(HTTPException) as exc_info:
            pdf_service._validate_file(mock_file)

        assert exc_info.value.status_code == 400
        assert "PDF files" in exc_info.value.detail

    def test_validate_file_too_large(self, pdf_service):
        """Test validation fails for files exceeding size limit."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "large.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = 51 * 1024 * 1024  # 51MB, exceeds 50MB limit

        with pytest.raises(HTTPException) as exc_info:
            pdf_service._validate_file(mock_file)

        assert exc_info.value.status_code == 413
        assert "too large" in exc_info.value.detail.lower()

    @pytest.mark.parametrize(
        "filename",
        ["test.PDF", "test.Pdf", "test.pDf"],
        ids=["uppercase", "titlecase", "mixedcase"],
    )
    def test_validate_file_case_insensitive_extension(self, pdf_service, filename):
        """Test validation accepts PDF files with different case extensions."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = filename
        mock_file.content_type = "application/pdf"
        mock_file.size = 1000

        # Should not raise an exception
        pdf_service._validate_file(mock_file)
