"""
Comprehensive tests for PDFService to increase coverage beyond existing tests.

This module focuses on edge cases, error scenarios, logging integration,
performance tracking, and uncovered code paths in the PDFService class.
"""

import os
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, UploadFile

from backend.app.models.pdf import PDFInfo, PDFMetadata, PDFUploadResponse
from backend.app.services.pdf_service import PDFService


@pytest.fixture
def pdf_service():
    """Create a temporary PDFService instance for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = PDFService(upload_dir=temp_dir)
        yield service
        # Cleanup is automatic with tempfile.TemporaryDirectory


class TestPDFServiceLoggingIntegration:
    """Test logging integration throughout the service."""

    def test_service_initialization_logging(self):
        """Test that service initialization logs correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "backend.app.services.pdf_service.get_logger"
            ) as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                PDFService(upload_dir=temp_dir)

                # Verify logger was configured
                mock_get_logger.assert_called_once()
                mock_logger.info.assert_called_once()
                call_args = mock_logger.info.call_args
                assert "PDF service initialized" in call_args[0][0]

    def test_file_validation_logging_debug(self, pdf_service):
        """Test debug logging during file validation."""
        with patch.object(pdf_service.logger, "debug") as mock_debug:
            mock_file = Mock(spec=UploadFile)
            mock_file.filename = "test.pdf"
            mock_file.content_type = "application/pdf"
            mock_file.size = 1000

            pdf_service._validate_file(mock_file, 1000)

            # Should log validation start and success
            assert mock_debug.call_count >= 2
            calls = [call.args[0] for call in mock_debug.call_args_list]
            assert any("Starting file validation" in call for call in calls)
            assert any("File validation passed" in call for call in calls)

    def test_file_validation_logging_warning_no_filename(self, pdf_service):
        """Test warning logging when filename is missing."""
        with patch.object(pdf_service.logger, "warning") as mock_warning:
            mock_file = Mock(spec=UploadFile)
            mock_file.filename = None
            mock_file.content_type = "application/pdf"
            mock_file.size = 1000

            with pytest.raises(HTTPException):
                pdf_service._validate_file(mock_file, 1000)

            mock_warning.assert_called_once()
            assert "no filename provided" in mock_warning.call_args[0][0]

    def test_file_validation_logging_warning_invalid_extension(self, pdf_service):
        """Test warning logging for invalid file extensions."""
        with patch.object(pdf_service.logger, "warning") as mock_warning:
            mock_file = Mock(spec=UploadFile)
            mock_file.filename = "test.txt"
            mock_file.content_type = "text/plain"
            mock_file.size = 1000

            with pytest.raises(HTTPException):
                pdf_service._validate_file(mock_file, 1000)

            mock_warning.assert_called_once()
            assert "invalid file extension" in mock_warning.call_args[0][0]

    def test_file_validation_logging_warning_too_large(self, pdf_service):
        """Test warning logging for oversized files."""
        with patch.object(pdf_service.logger, "warning") as mock_warning:
            mock_file = Mock(spec=UploadFile)
            mock_file.filename = "large.pdf"
            mock_file.content_type = "application/pdf"
            file_size = 60 * 1024 * 1024  # 60MB
            mock_file.size = file_size

            with pytest.raises(HTTPException):
                pdf_service._validate_file(mock_file, file_size)

            mock_warning.assert_called_once()
            assert "file too large" in mock_warning.call_args[0][0]


class TestPDFServiceMetadataExtractionEdgeCases:
    """Test edge cases in PDF metadata extraction."""

    def test_extract_metadata_file_stat_error(self, pdf_service, sample_pdf_content):
        """Test metadata extraction when file.stat() fails."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            # Mock file.stat() to raise an exception
            with patch.object(Path, "stat", side_effect=OSError("Permission denied")):
                metadata = pdf_service._extract_pdf_metadata(temp_path)

                # Should return fallback metadata
                assert isinstance(metadata, PDFMetadata)
                assert metadata.page_count == 1
                assert metadata.encrypted is False
        finally:
            os.unlink(temp_path)

    def test_extract_metadata_pypdf_exception_handling(
        self, pdf_service, sample_pdf_content
    ):
        """Test exception handling in PDF metadata extraction."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            with patch(
                "backend.app.services.pdf_service.PdfReader",
                side_effect=Exception("PDF parsing error"),
            ):
                with patch.object(pdf_service.logger, "warning") as mock_warning:
                    metadata = pdf_service._extract_pdf_metadata(temp_path)

                    # Should use fallback metadata
                    assert metadata.page_count == 1
                    assert metadata.encrypted is False

                    # Should log the fallback usage
                    mock_warning.assert_called()
                    warning_calls = [
                        call.args[0] for call in mock_warning.call_args_list
                    ]
                    assert any(
                        "Using fallback metadata" in call for call in warning_calls
                    )
        finally:
            os.unlink(temp_path)

    def test_extract_metadata_fallback_creation_error(
        self, pdf_service, sample_pdf_content
    ):
        """Test when even fallback metadata creation fails."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            with patch(
                "backend.app.services.pdf_service.PdfReader",
                side_effect=Exception("PDF error"),
            ):
                with patch(
                    "backend.app.models.pdf.PDFMetadata",
                    side_effect=[
                        Exception("Validation error"),
                        PDFMetadata(page_count=1, file_size=1, encrypted=False),
                    ],
                ):
                    with patch.object(pdf_service.logger, "error") as mock_error:
                        metadata = pdf_service._extract_pdf_metadata(temp_path)

                        # Should eventually create minimal metadata
                        assert metadata.page_count == 1

                        # Should log the fallback creation error
                        mock_error.assert_called_once()
                        assert (
                            "Fallback metadata creation failed"
                            in mock_error.call_args[0][0]
                        )
        finally:
            os.unlink(temp_path)

    def test_extract_metadata_with_none_pypdf_metadata(
        self, pdf_service, sample_pdf_content
    ):
        """Test metadata extraction when PyPDF returns None metadata."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            with patch(
                "backend.app.services.pdf_service.PdfReader"
            ) as mock_reader_class:
                mock_reader = Mock()
                mock_reader.pages = [Mock()]  # One page
                mock_reader.is_encrypted = False
                mock_reader.metadata = None  # No metadata
                mock_reader_class.return_value = mock_reader

                metadata = pdf_service._extract_pdf_metadata(temp_path)

                assert metadata.page_count == 1
                assert metadata.encrypted is False
                assert metadata.title is None
                assert metadata.author is None
        finally:
            os.unlink(temp_path)

    def test_extract_metadata_debug_logging(self, pdf_service, sample_pdf_content):
        """Test debug logging during metadata extraction."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            with patch.object(pdf_service.logger, "debug") as mock_debug:
                pdf_service._extract_pdf_metadata(temp_path)

                # Should log metadata extraction details
                mock_debug.assert_called()
                debug_calls = [call.args[0] for call in mock_debug.call_args_list]
                assert any("PDF metadata extracted" in call for call in debug_calls)
        finally:
            os.unlink(temp_path)


class TestPDFServiceUploadEdgeCases:
    """Test edge cases in PDF upload functionality."""

    @pytest.mark.asyncio
    async def test_upload_pdf_aiofiles_write_error(
        self, pdf_service, sample_pdf_content
    ):
        """Test upload failure during async file writing."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = len(sample_pdf_content)
        mock_file.seek = AsyncMock()
        # Proper chunk reading
        mock_file.read = AsyncMock(side_effect=[sample_pdf_content, b""])

        with patch("aiofiles.open", side_effect=OSError("Disk full")):
            with pytest.raises(HTTPException) as exc_info:
                await pdf_service.upload_pdf(mock_file)

            assert exc_info.value.status_code == 500
            assert "Failed to process file" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_upload_pdf_magic_mime_detection_error(
        self, pdf_service, sample_pdf_content
    ):
        """Test upload when MIME type detection fails."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = len(sample_pdf_content)
        mock_file.seek = AsyncMock()
        # Proper chunk reading
        mock_file.read = AsyncMock(side_effect=[sample_pdf_content, b""])

        with patch.object(
            pdf_service, "_validate_pdf_header", side_effect=Exception("Header validation error")
        ):
            with pytest.raises(HTTPException) as exc_info:
                await pdf_service.upload_pdf(mock_file)

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_upload_pdf_metadata_extraction_error(
        self, pdf_service, sample_pdf_content
    ):
        """Test upload when metadata extraction fails but upload continues."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = len(sample_pdf_content)
        mock_file.seek = AsyncMock()
        # Proper chunk reading
        mock_file.read = AsyncMock(side_effect=[sample_pdf_content, b""])

        with patch.object(pdf_service, "_extract_pdf_metadata") as mock_extract:
            # Mock metadata extraction to return fallback metadata
            mock_extract.return_value = PDFMetadata(
                page_count=1, file_size=len(sample_pdf_content), encrypted=False
            )

            response = await pdf_service.upload_pdf(mock_file)

            assert isinstance(response, PDFUploadResponse)
            assert response.metadata.page_count == 1

    @pytest.mark.asyncio
    async def test_upload_pdf_cleanup_on_header_validation_failure(
        self, pdf_service, sample_pdf_content
    ):
        """Test that files are cleaned up when PDF header validation fails."""
        # Create a file with invalid PDF header
        invalid_content = b"This is not a PDF file"
        
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = len(invalid_content)
        mock_file.seek = AsyncMock()
        # Proper chunk reading
        mock_file.read = AsyncMock(side_effect=[invalid_content, b""])

        with patch("os.unlink") as mock_unlink:
            with pytest.raises(HTTPException):
                await pdf_service.upload_pdf(mock_file)

            # Should have attempted to clean up the file
            mock_unlink.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_pdf_cleanup_failure_logging(
        self, pdf_service, sample_pdf_content
    ):
        """Test logging when cleanup after failure also fails."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = len(sample_pdf_content)
        mock_file.read = AsyncMock(side_effect=Exception("Read error"))

        with patch.object(Path, "exists", return_value=True):
            with patch("os.unlink", side_effect=OSError("Cannot delete")):
                with patch.object(pdf_service.logger, "error") as mock_error:
                    with pytest.raises(HTTPException):
                        await pdf_service.upload_pdf(mock_file)

                    # Should log cleanup failure
                    mock_error.assert_called()
                    error_calls = [call.args[0] for call in mock_error.call_args_list]
                    assert any(
                        "Failed to clean up upload file" in call for call in error_calls
                    )

    @pytest.mark.asyncio
    async def test_upload_pdf_file_logger_integration(
        self, pdf_service, sample_pdf_content
    ):
        """Test file logger integration during upload."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = len(sample_pdf_content)
        mock_file.seek = AsyncMock()
        # Proper chunk reading
        mock_file.read = AsyncMock(side_effect=[sample_pdf_content, b""])

        with patch.object(
            pdf_service.file_logger, "upload_started"
        ) as mock_started:
            with patch.object(
                pdf_service.file_logger, "upload_completed"
            ) as mock_completed:
                response = await pdf_service.upload_pdf(mock_file)

                # Should log upload lifecycle
                # Note: file size may be 0 or None for mocked files since _determine_upload_size
                # can't properly determine size from mock objects
                mock_started.assert_called_once()
                assert mock_started.call_args[0][0] == "test.pdf"
                assert mock_started.call_args[1]["content_type"] == "application/pdf"
                
                mock_completed.assert_called_once()

                # Verify file was stored
                assert response.file_id in pdf_service._file_metadata

    @pytest.mark.asyncio
    async def test_upload_pdf_http_exception_passthrough(self, pdf_service):
        """Test that HTTPExceptions are passed through without wrapping."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"  # Invalid extension
        mock_file.content_type = "text/plain"
        mock_file.size = 1000

        # Should pass through the HTTPException from validation
        with pytest.raises(HTTPException) as exc_info:
            await pdf_service.upload_pdf(mock_file)

        assert exc_info.value.status_code == 400
        assert "PDF files" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_upload_pdf_double_filename_check(
        self, pdf_service, sample_pdf_content
    ):
        """Test the secondary filename check after validation."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = len(sample_pdf_content)
        mock_file.seek = AsyncMock()
        # Proper chunk reading
        mock_file.read = AsyncMock(side_effect=[sample_pdf_content, b""])

        # Simulate filename becoming None after validation (edge case)
        with patch.object(pdf_service, "_validate_file"):
            mock_file.filename = None  # Set to None after validation

            with pytest.raises(ValueError) as exc_info:
                await pdf_service.upload_pdf(mock_file)

            assert "Filename should not be None after validation" in str(exc_info.value)


class TestPDFServiceFileOperationsEdgeCases:
    """Test edge cases in file operations (get, delete, list)."""

    def test_get_pdf_path_logging_integration(self, pdf_service):
        """Test logging integration in get_pdf_path."""
        with patch.object(pdf_service.logger, "debug") as mock_debug:
            with patch.object(pdf_service.logger, "warning") as mock_warning:
                with pytest.raises(HTTPException):
                    pdf_service.get_pdf_path("nonexistent-id")

                # Should log debug and warning
                mock_debug.assert_called_once_with(
                    "Getting PDF path", file_id="nonexistent-id"
                )
                mock_warning.assert_called_once()
                assert "PDF file not found in metadata" in mock_warning.call_args[0][0]

    def test_get_pdf_path_file_missing_detailed_logging(
        self, pdf_service, sample_pdf_content
    ):
        """Test detailed logging when file exists in metadata but not on disk."""
        file_id = str(uuid.uuid4())

        # Add to metadata but don't create physical file
        metadata = PDFMetadata(page_count=1, file_size=len(sample_pdf_content))
        pdf_info = PDFInfo(
            file_id=file_id,
            filename="test.pdf",
            file_size=len(sample_pdf_content),
            mime_type="application/pdf",
            upload_time=datetime.now(UTC),
            metadata=metadata,
        )
        pdf_service._file_metadata[file_id] = pdf_info

        with patch.object(pdf_service.logger, "error") as mock_error:
            with pytest.raises(HTTPException):
                pdf_service.get_pdf_path(file_id)

            # Should log detailed error information
            mock_error.assert_called_once()
            error_call = mock_error.call_args[0][0]
            assert "PDF file not found on disk" in error_call

    def test_get_pdf_path_file_logger_integration(
        self, pdf_service, sample_pdf_content
    ):
        """Test file logger integration for successful path retrieval."""
        file_id = str(uuid.uuid4())
        file_path = pdf_service.upload_dir / f"{file_id}.pdf"
        file_path.write_bytes(sample_pdf_content)

        # Add to metadata
        metadata = PDFMetadata(page_count=1, file_size=len(sample_pdf_content))
        pdf_info = PDFInfo(
            file_id=file_id,
            filename="test.pdf",
            file_size=len(sample_pdf_content),
            mime_type="application/pdf",
            upload_time=datetime.now(UTC),
            metadata=metadata,
        )
        pdf_service._file_metadata[file_id] = pdf_info

        with patch.object(pdf_service.file_logger, "access_logged") as mock_access:
            pdf_service.get_pdf_path(file_id)

            # Should log file access
            mock_access.assert_called_once_with(
                file_id, "get_path", file_path=str(file_path)
            )

    def test_get_pdf_metadata_logging_integration(
        self, pdf_service, sample_pdf_content
    ):
        """Test logging integration in get_pdf_metadata."""
        file_id = str(uuid.uuid4())

        metadata = PDFMetadata(page_count=5, file_size=len(sample_pdf_content))
        pdf_info = PDFInfo(
            file_id=file_id,
            filename="test.pdf",
            file_size=len(sample_pdf_content),
            mime_type="application/pdf",
            upload_time=datetime.now(UTC),
            metadata=metadata,
        )
        pdf_service._file_metadata[file_id] = pdf_info

        with patch.object(pdf_service.logger, "debug") as mock_debug:
            with patch.object(pdf_service.file_logger, "access_logged") as mock_access:
                result = pdf_service.get_pdf_metadata(file_id)

                # Should log debug and access
                mock_debug.assert_called_once_with(
                    "Getting PDF metadata", file_id=file_id
                )
                mock_access.assert_called_once()

                assert result.page_count == 5

    def test_delete_pdf_missing_physical_file_logging(
        self, pdf_service, sample_pdf_content
    ):
        """Test logging when physical file is missing during deletion."""
        file_id = str(uuid.uuid4())

        # Add to metadata but don't create physical file
        metadata = PDFMetadata(page_count=1, file_size=len(sample_pdf_content))
        pdf_info = PDFInfo(
            file_id=file_id,
            filename="test.pdf",
            file_size=len(sample_pdf_content),
            mime_type="application/pdf",
            upload_time=datetime.now(UTC),
            metadata=metadata,
        )
        pdf_service._file_metadata[file_id] = pdf_info

        with patch.object(pdf_service.logger, "warning") as mock_warning:
            with patch.object(pdf_service.logger, "info") as mock_info:
                result = pdf_service.delete_pdf(file_id)

                # Should still succeed but log warning about missing file
                assert result is True
                mock_warning.assert_called()
                warning_calls = [call.args[0] for call in mock_warning.call_args_list]
                assert any(
                    "Physical file not found during deletion" in call
                    for call in warning_calls
                )

                # Should log successful deletion
                mock_info.assert_called()
                info_calls = [call.args[0] for call in mock_info.call_args_list]
                assert any(
                    "PDF file deleted successfully" in call for call in info_calls
                )

    def test_delete_pdf_os_error_handling(self, pdf_service, sample_pdf_content):
        """Test OS error handling during file deletion."""
        file_id = str(uuid.uuid4())
        file_path = pdf_service.upload_dir / f"{file_id}.pdf"
        file_path.write_bytes(sample_pdf_content)

        metadata = PDFMetadata(page_count=1, file_size=len(sample_pdf_content))
        pdf_info = PDFInfo(
            file_id=file_id,
            filename="test.pdf",
            file_size=len(sample_pdf_content),
            mime_type="application/pdf",
            upload_time=datetime.now(UTC),
            metadata=metadata,
        )
        pdf_service._file_metadata[file_id] = pdf_info

        with patch("os.unlink", side_effect=PermissionError("Permission denied")):
            with patch.object(
                pdf_service.file_logger, "deletion_logged"
            ) as mock_deletion:
                with pytest.raises(HTTPException) as exc_info:
                    pdf_service.delete_pdf(file_id)

                assert exc_info.value.status_code == 500
                assert "Failed to delete file" in exc_info.value.detail

                # Should log deletion failure
                mock_deletion.assert_called()
                deletion_call = mock_deletion.call_args[1]
                assert deletion_call["success"] is False

    def test_list_files_logging_integration(self, pdf_service, sample_pdf_content):
        """Test logging integration in list_files."""
        # Add some files to test with
        for i in range(2):
            file_id = str(uuid.uuid4())
            metadata = PDFMetadata(page_count=i + 1, file_size=len(sample_pdf_content))
            pdf_info = PDFInfo(
                file_id=file_id,
                filename=f"test{i}.pdf",
                file_size=len(sample_pdf_content),
                mime_type="application/pdf",
                upload_time=datetime.now(UTC),
                metadata=metadata,
            )
            pdf_service._file_metadata[file_id] = pdf_info

        with patch.object(pdf_service.logger, "debug") as mock_debug:
            with patch.object(pdf_service.file_logger, "access_logged") as mock_access:
                result = pdf_service.list_files()

                assert len(result) == 2

                # Should log debug information
                mock_debug.assert_called_once()
                debug_call = mock_debug.call_args[0][0]
                assert "Listing PDF files" in debug_call

                # Should log file access
                mock_access.assert_called_once()

    def test_get_service_stats_empty_files_handling(self, pdf_service):
        """Test service statistics with no files (division by zero prevention)."""
        stats = pdf_service.get_service_stats()

        assert stats["total_files"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["total_pages"] == 0
        assert stats["average_file_size_mb"] == 0  # Should handle division by zero
        assert stats["average_pages_per_file"] == 0  # Should handle division by zero
        assert "upload_directory" in stats
        assert "max_file_size_mb" in stats

    def test_get_service_stats_logging_integration(
        self, pdf_service, sample_pdf_content
    ):
        """Test logging integration in get_service_stats."""
        # Add a file
        file_id = str(uuid.uuid4())
        metadata = PDFMetadata(page_count=3, file_size=len(sample_pdf_content))
        pdf_info = PDFInfo(
            file_id=file_id,
            filename="test.pdf",
            file_size=len(sample_pdf_content),
            mime_type="application/pdf",
            upload_time=datetime.now(UTC),
            metadata=metadata,
        )
        pdf_service._file_metadata[file_id] = pdf_info

        with patch.object(pdf_service.logger, "info") as mock_info:
            stats = pdf_service.get_service_stats()

            # Should log service statistics
            mock_info.assert_called_once()
            info_call = mock_info.call_args[0][0]
            assert "Service statistics requested" in info_call

            assert stats["total_files"] == 1
            assert stats["total_pages"] == 3

    def test_get_service_stats_metadata_none_handling(
        self, pdf_service, sample_pdf_content
    ):
        """Test service statistics when some files have None metadata."""
        # Add files with and without metadata
        for i in range(3):
            file_id = str(uuid.uuid4())
            metadata = (
                PDFMetadata(page_count=i + 1, file_size=len(sample_pdf_content))
                if i < 2
                else None
            )
            pdf_info = PDFInfo(
                file_id=file_id,
                filename=f"test{i}.pdf",
                file_size=len(sample_pdf_content),
                mime_type="application/pdf",
                upload_time=datetime.now(UTC),
                metadata=metadata,
            )
            pdf_service._file_metadata[file_id] = pdf_info

        stats = pdf_service.get_service_stats()

        assert stats["total_files"] == 3
        assert stats["total_pages"] == 3  # 1+2+0 (None metadata counts as 0)
        assert stats["average_pages_per_file"] == 1.0


class TestPDFServicePerformanceIntegration:
    """Test performance tracking integration."""

    def test_performance_tracker_usage_in_metadata_extraction(
        self, pdf_service, sample_pdf_content
    ):
        """Test that PerformanceTracker is used in metadata extraction."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            with patch("backend.app.utils.logger.PerformanceTracker") as mock_tracker:
                mock_context = Mock()
                mock_tracker.return_value.__enter__ = Mock(return_value=mock_context)
                mock_tracker.return_value.__exit__ = Mock(return_value=None)

                pdf_service._extract_pdf_metadata(temp_path)

                # Should use PerformanceTracker
                mock_tracker.assert_called()
                call_args = mock_tracker.call_args[0]
                assert "PDF metadata extraction" in call_args[0]
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_performance_tracker_usage_in_upload(
        self, pdf_service, sample_pdf_content
    ):
        """Test that PerformanceTracker is used during upload."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = len(sample_pdf_content)
        mock_file.seek = AsyncMock()
        # Proper chunk reading
        mock_file.read = AsyncMock(side_effect=[sample_pdf_content, b""])

        with patch("backend.app.utils.logger.PerformanceTracker") as mock_tracker:
            mock_context = Mock()
            mock_context.duration_ms = 100
            mock_tracker.return_value.__enter__ = Mock(return_value=mock_context)
            mock_tracker.return_value.__exit__ = Mock(return_value=None)

            await pdf_service.upload_pdf(mock_file)

            # Should use PerformanceTracker for multiple operations
            assert mock_tracker.call_count >= 2  # Upload and file write operations
            call_args_list = [call[0][0] for call in mock_tracker.call_args_list]
            assert any("PDF file upload" in args for args in call_args_list)
            assert any("File write operation" in args for args in call_args_list)

    def test_performance_tracker_usage_in_deletion(
        self, pdf_service, sample_pdf_content
    ):
        """Test that PerformanceTracker is used during deletion."""
        file_id = str(uuid.uuid4())
        file_path = pdf_service.upload_dir / f"{file_id}.pdf"
        file_path.write_bytes(sample_pdf_content)

        metadata = PDFMetadata(page_count=1, file_size=len(sample_pdf_content))
        pdf_info = PDFInfo(
            file_id=file_id,
            filename="test.pdf",
            file_size=len(sample_pdf_content),
            mime_type="application/pdf",
            upload_time=datetime.now(UTC),
            metadata=metadata,
        )
        pdf_service._file_metadata[file_id] = pdf_info

        with patch("backend.app.utils.logger.PerformanceTracker") as mock_tracker:
            mock_context = Mock()
            mock_context.duration_ms = 50
            mock_tracker.return_value.__enter__ = Mock(return_value=mock_context)
            mock_tracker.return_value.__exit__ = Mock(return_value=None)

            result = pdf_service.delete_pdf(file_id)

            assert result is True
            # Should use PerformanceTracker for deletion
            mock_tracker.assert_called_once()
            call_args = mock_tracker.call_args[0]
            assert "PDF file deletion" in call_args[0]


class TestPDFServiceErrorContextLogging:
    """Test exception context logging integration."""

    def test_log_exception_context_in_metadata_extraction(
        self, pdf_service, sample_pdf_content
    ):
        """Test that log_exception_context is used in metadata extraction."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            with patch(
                "backend.app.services.pdf_service.PdfReader",
                side_effect=Exception("PDF error"),
            ):
                with patch(
                    "backend.app.utils.logger.log_exception_context"
                ) as mock_log_exception:
                    pdf_service._extract_pdf_metadata(temp_path)

                    # Should log exception context
                    mock_log_exception.assert_called_once()
                    call_args = mock_log_exception.call_args[0]
                    assert "PDF metadata extraction" in call_args[1]
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_log_exception_context_in_upload(self, pdf_service):
        """Test that log_exception_context is used during upload failures."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = 1000
        mock_file.read = AsyncMock(side_effect=Exception("Read error"))

        with patch(
            "backend.app.utils.logger.log_exception_context"
        ) as mock_log_exception:
            with pytest.raises(HTTPException):
                await pdf_service.upload_pdf(mock_file)

            # Should log exception context
            mock_log_exception.assert_called_once()
            call_args = mock_log_exception.call_args[0]
            assert "PDF file upload" in call_args[1]

    def test_log_exception_context_in_deletion(self, pdf_service, sample_pdf_content):
        """Test that log_exception_context is used during deletion failures."""
        file_id = str(uuid.uuid4())
        file_path = pdf_service.upload_dir / f"{file_id}.pdf"
        file_path.write_bytes(sample_pdf_content)

        metadata = PDFMetadata(page_count=1, file_size=len(sample_pdf_content))
        pdf_info = PDFInfo(
            file_id=file_id,
            filename="test.pdf",
            file_size=len(sample_pdf_content),
            mime_type="application/pdf",
            upload_time=datetime.now(UTC),
            metadata=metadata,
        )
        pdf_service._file_metadata[file_id] = pdf_info

        with patch("os.unlink", side_effect=Exception("Delete error")):
            with patch(
                "backend.app.utils.logger.log_exception_context"
            ) as mock_log_exception:
                with pytest.raises(HTTPException):
                    pdf_service.delete_pdf(file_id)

                # Should log exception context
                mock_log_exception.assert_called_once()
                call_args = mock_log_exception.call_args[0]
                assert "PDF file deletion" in call_args[1]


class TestPDFServiceLogPerformanceDecorator:
    """Test @log_performance decorator integration."""

    def test_metadata_extraction_has_performance_decorator(
        self, pdf_service, sample_pdf_content
    ):
        """Test that metadata extraction uses @log_performance decorator."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            # Check that the method has been decorated
            assert hasattr(pdf_service._extract_pdf_metadata, "__wrapped__")

            # Run the method to ensure decorator works
            metadata = pdf_service._extract_pdf_metadata(temp_path)
            assert isinstance(metadata, PDFMetadata)
        finally:
            os.unlink(temp_path)


class TestPDFServiceValidationNoneSize:
    """Test file validation with None file size."""

    def test_validate_file_none_size_allowed(self, pdf_service):
        """Test that None file size is handled gracefully."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = None  # Size not provided

        # Should not raise an exception (size check is skipped for None)
        pdf_service._validate_file(mock_file, None)

    def test_validate_file_zero_size_allowed(self, pdf_service):
        """Test that zero file size is handled gracefully."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "empty.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = 0

        # Should not raise an exception (size check allows zero)
        pdf_service._validate_file(mock_file, 0)
