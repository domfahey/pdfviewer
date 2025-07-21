"""
Comprehensive unit tests for PDFService class.

Tests cover file upload validation, metadata extraction, error handling,
performance tracking, and all public methods of the PDFService.
"""

import tempfile
import uuid
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, UploadFile

from backend.app.models.pdf import PDFMetadata, PDFUploadResponse
from backend.app.services.pdf_service import PDFService


class TestPDFServiceInitialization:
    """Test PDFService initialization and configuration."""

    def test_init_default_upload_dir(self):
        """Test PDFService initialization with default upload directory."""
        service = PDFService()

        assert service.upload_dir == Path("uploads")
        assert service.upload_dir.exists()
        assert service.max_file_size == 50 * 1024 * 1024  # 50MB
        assert service.allowed_mime_types == {"application/pdf"}

    def test_init_custom_upload_dir(self):
        """Test PDFService initialization with custom upload directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = PDFService(upload_dir=temp_dir)

            assert service.upload_dir == Path(temp_dir)
            assert service.upload_dir.exists()

    def test_init_creates_upload_directory(self):
        """Test that initialization creates the upload directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_path = Path(temp_dir) / "new_uploads"
            assert not upload_path.exists()

            service = PDFService(upload_dir=str(upload_path))

            assert upload_path.exists()
            assert service.upload_dir == upload_path


class TestPDFServiceValidation:
    """Test file validation methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PDFService(upload_dir="test_uploads")

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up test upload directory if it exists
        if self.service.upload_dir.exists():
            import shutil

            shutil.rmtree(self.service.upload_dir, ignore_errors=True)

    def test_validate_file_valid_pdf(self, sample_pdf_content):
        """Test validation of a valid PDF file."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = len(sample_pdf_content)

        # Should not raise an exception
        self.service._validate_file(mock_file)

    def test_validate_file_no_filename(self):
        """Test validation fails when no filename is provided."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = None
        mock_file.content_type = "application/pdf"
        mock_file.size = 1000

        with pytest.raises(HTTPException) as exc_info:
            self.service._validate_file(mock_file)

        assert exc_info.value.status_code == 400
        assert "filename" in exc_info.value.detail.lower()

    def test_validate_file_empty_filename(self):
        """Test validation fails when filename is empty."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = ""
        mock_file.content_type = "application/pdf"
        mock_file.size = 1000

        with pytest.raises(HTTPException) as exc_info:
            self.service._validate_file(mock_file)

        assert exc_info.value.status_code == 400

    def test_validate_file_invalid_extension(self):
        """Test validation fails for non-PDF file extensions."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.size = 1000

        with pytest.raises(HTTPException) as exc_info:
            self.service._validate_file(mock_file)

        assert exc_info.value.status_code == 400
        assert "PDF files" in exc_info.value.detail

    def test_validate_file_too_large(self):
        """Test validation fails for files exceeding size limit."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "large.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = 51 * 1024 * 1024  # 51MB, exceeds 50MB limit

        with pytest.raises(HTTPException) as exc_info:
            self.service._validate_file(mock_file)

        assert exc_info.value.status_code == 413
        assert "too large" in exc_info.value.detail.lower()

    def test_validate_file_case_insensitive_extension(self):
        """Test validation accepts PDF files with different case extensions."""
        test_cases = ["test.PDF", "test.Pdf", "test.pDf"]

        for filename in test_cases:
            mock_file = Mock(spec=UploadFile)
            mock_file.filename = filename
            mock_file.content_type = "application/pdf"
            mock_file.size = 1000

            # Should not raise an exception
            self.service._validate_file(mock_file)


class TestPDFServiceMetadataExtraction:
    """Test PDF metadata extraction functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PDFService(upload_dir="test_uploads")

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.service.upload_dir.exists():
            import shutil

            shutil.rmtree(self.service.upload_dir, ignore_errors=True)

    def test_extract_pdf_metadata_valid_file(self, sample_pdf_file):
        """Test metadata extraction from a valid PDF file."""
        metadata = self.service._extract_pdf_metadata(sample_pdf_file)

        assert isinstance(metadata, PDFMetadata)
        assert metadata.page_count > 0
        assert metadata.file_size > 0
        assert metadata.encrypted is False

        # Test computed fields
        assert hasattr(metadata, "file_size_mb")
        assert hasattr(metadata, "document_complexity_score")
        assert hasattr(metadata, "document_category")

    @patch("backend.app.services.pdf_service.PdfReader")
    def test_extract_pdf_metadata_corrupted_file(
        self, mock_pdf_reader, sample_pdf_file
    ):
        """Test metadata extraction handles corrupted PDF files gracefully."""
        # Mock PdfReader to raise an exception
        mock_pdf_reader.side_effect = Exception("Corrupted PDF")

        metadata = self.service._extract_pdf_metadata(sample_pdf_file)

        # Should return fallback metadata
        assert isinstance(metadata, PDFMetadata)
        assert metadata.page_count == 1  # Fallback value
        assert metadata.encrypted is False  # Safe default

    @patch("backend.app.services.pdf_service.PdfReader")
    def test_extract_pdf_metadata_with_metadata_validation_error(
        self, mock_pdf_reader, sample_pdf_file
    ):
        """Test handling of metadata validation errors."""
        # Mock PdfReader to return problematic metadata
        mock_reader = Mock()
        mock_reader.pages = [Mock()]  # One page
        mock_reader.is_encrypted = False
        mock_reader.metadata = Mock()

        # Set up metadata that will cause validation errors
        mock_reader.metadata.title = "x" * 600  # Exceeds max length
        mock_reader.metadata.creation_date = None

        mock_pdf_reader.return_value = mock_reader

        metadata = self.service._extract_pdf_metadata(sample_pdf_file)

        # Should use fallback metadata when validation fails
        assert isinstance(metadata, PDFMetadata)
        assert metadata.page_count == 1

    @patch("backend.app.services.pdf_service.PdfReader")
    def test_extract_pdf_metadata_encrypted_pdf(self, mock_pdf_reader, sample_pdf_file):
        """Test metadata extraction from encrypted PDF."""
        mock_reader = Mock()
        mock_reader.pages = [Mock(), Mock()]  # Two pages
        mock_reader.is_encrypted = True
        mock_reader.metadata = None

        mock_pdf_reader.return_value = mock_reader

        metadata = self.service._extract_pdf_metadata(sample_pdf_file)

        assert metadata.page_count == 2
        assert metadata.encrypted is True
        assert metadata.title is None  # No metadata available


class TestPDFServiceUpload:
    """Test PDF upload functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PDFService(upload_dir="test_uploads")

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.service.upload_dir.exists():
            import shutil

            shutil.rmtree(self.service.upload_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_upload_pdf_success(self, sample_pdf_content):
        """Test successful PDF upload."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = len(sample_pdf_content)
        mock_file.read = Mock(return_value=sample_pdf_content)

        with patch("magic.from_file", return_value="application/pdf"):
            response = await self.service.upload_pdf(mock_file)

        assert isinstance(response, PDFUploadResponse)
        assert response.filename == "test.pdf"
        assert response.mime_type == "application/pdf"
        assert response.file_size == len(sample_pdf_content)
        assert response.metadata is not None

        # Verify file was stored
        assert len(self.service._file_metadata) == 1
        assert response.file_id in self.service._file_metadata

    @pytest.mark.asyncio
    async def test_upload_pdf_invalid_mime_type(self, sample_pdf_content):
        """Test upload failure due to invalid MIME type detected."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = len(sample_pdf_content)
        mock_file.read = Mock(return_value=sample_pdf_content)

        with patch("magic.from_file", return_value="text/plain"):
            with pytest.raises(HTTPException) as exc_info:
                await self.service.upload_pdf(mock_file)

        assert exc_info.value.status_code == 400
        assert "Invalid file type" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_upload_pdf_file_write_error(self, sample_pdf_content):
        """Test upload failure due to file write error."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = len(sample_pdf_content)
        mock_file.read = Mock(return_value=sample_pdf_content)

        # Make upload directory read-only to cause write error
        self.service.upload_dir.chmod(0o444)

        try:
            with pytest.raises(HTTPException) as exc_info:
                await self.service.upload_pdf(mock_file)

            assert exc_info.value.status_code == 500
            assert "Failed to process file" in exc_info.value.detail
        finally:
            # Restore permissions for cleanup
            self.service.upload_dir.chmod(0o755)


class TestPDFServiceFileOperations:
    """Test PDF file operations (get, delete, list)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PDFService(upload_dir="test_uploads")

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.service.upload_dir.exists():
            import shutil

            shutil.rmtree(self.service.upload_dir, ignore_errors=True)

    def test_get_pdf_path_success(self, sample_pdf_content):
        """Test successful PDF path retrieval."""
        # Add a file to metadata and create the actual file
        file_id = str(uuid.uuid4())
        file_path = self.service.upload_dir / f"{file_id}.pdf"
        file_path.write_bytes(sample_pdf_content)

        # Add to metadata (simplified - normally done by upload_pdf)
        from datetime import datetime, timezone

        from backend.app.models.pdf import PDFInfo, PDFMetadata

        metadata = PDFMetadata(page_count=1, file_size=len(sample_pdf_content))
        pdf_info = PDFInfo(
            file_id=file_id,
            filename="test.pdf",
            file_size=len(sample_pdf_content),
            mime_type="application/pdf",
            upload_time=datetime.now(timezone.utc),
            metadata=metadata,
        )
        self.service._file_metadata[file_id] = pdf_info

        result_path = self.service.get_pdf_path(file_id)
        assert result_path == file_path
        assert result_path.exists()

    def test_get_pdf_path_not_found(self):
        """Test PDF path retrieval for non-existent file."""
        with pytest.raises(HTTPException) as exc_info:
            self.service.get_pdf_path("nonexistent-id")

        assert exc_info.value.status_code == 404
        assert "File not found" in exc_info.value.detail

    def test_get_pdf_path_file_missing_on_disk(self):
        """Test PDF path retrieval when metadata exists but file is missing on disk."""
        file_id = str(uuid.uuid4())

        # Add to metadata but don't create the actual file
        from datetime import datetime, timezone

        from backend.app.models.pdf import PDFInfo, PDFMetadata

        metadata = PDFMetadata(page_count=1, file_size=1000)
        pdf_info = PDFInfo(
            file_id=file_id,
            filename="test.pdf",
            file_size=1000,
            mime_type="application/pdf",
            upload_time=datetime.now(timezone.utc),
            metadata=metadata,
        )
        self.service._file_metadata[file_id] = pdf_info

        with pytest.raises(HTTPException) as exc_info:
            self.service.get_pdf_path(file_id)

        assert exc_info.value.status_code == 404
        assert "File not found on disk" in exc_info.value.detail

    def test_delete_pdf_success(self, sample_pdf_content):
        """Test successful PDF deletion."""
        # Set up a file for deletion
        file_id = str(uuid.uuid4())
        file_path = self.service.upload_dir / f"{file_id}.pdf"
        file_path.write_bytes(sample_pdf_content)

        from datetime import datetime, timezone

        from backend.app.models.pdf import PDFInfo, PDFMetadata

        metadata = PDFMetadata(page_count=1, file_size=len(sample_pdf_content))
        pdf_info = PDFInfo(
            file_id=file_id,
            filename="test.pdf",
            file_size=len(sample_pdf_content),
            mime_type="application/pdf",
            upload_time=datetime.now(timezone.utc),
            metadata=metadata,
        )
        self.service._file_metadata[file_id] = pdf_info

        # Delete the file
        result = self.service.delete_pdf(file_id)

        assert result is True
        assert not file_path.exists()
        assert file_id not in self.service._file_metadata

    def test_delete_pdf_not_found(self):
        """Test PDF deletion for non-existent file."""
        with pytest.raises(HTTPException) as exc_info:
            self.service.delete_pdf("nonexistent-id")

        assert exc_info.value.status_code == 404
        assert "File not found" in exc_info.value.detail

    def test_list_files_empty(self):
        """Test listing files when no files are uploaded."""
        result = self.service.list_files()

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_list_files_with_content(self, sample_pdf_content):
        """Test listing files with uploaded content."""
        # Add a file to metadata
        file_id = str(uuid.uuid4())

        from datetime import datetime, timezone

        from backend.app.models.pdf import PDFInfo, PDFMetadata

        metadata = PDFMetadata(page_count=1, file_size=len(sample_pdf_content))
        pdf_info = PDFInfo(
            file_id=file_id,
            filename="test.pdf",
            file_size=len(sample_pdf_content),
            mime_type="application/pdf",
            upload_time=datetime.now(timezone.utc),
            metadata=metadata,
        )
        self.service._file_metadata[file_id] = pdf_info

        result = self.service.list_files()

        assert isinstance(result, dict)
        assert len(result) == 1
        assert file_id in result
        assert result[file_id].filename == "test.pdf"

    def test_get_service_stats(self, sample_pdf_content):
        """Test getting service statistics."""
        # Add multiple files to test statistics
        for i in range(3):
            file_id = str(uuid.uuid4())

            from datetime import datetime, timezone

            from backend.app.models.pdf import PDFInfo, PDFMetadata

            metadata = PDFMetadata(page_count=i + 1, file_size=len(sample_pdf_content))
            pdf_info = PDFInfo(
                file_id=file_id,
                filename=f"test{i}.pdf",
                file_size=len(sample_pdf_content),
                mime_type="application/pdf",
                upload_time=datetime.now(timezone.utc),
                metadata=metadata,
            )
            self.service._file_metadata[file_id] = pdf_info

        stats = self.service.get_service_stats()

        assert stats["total_files"] == 3
        assert stats["total_pages"] == 6  # 1+2+3
        assert stats["total_size_bytes"] == len(sample_pdf_content) * 3
        assert stats["average_pages_per_file"] == 2.0
        assert "upload_directory" in stats
        assert "max_file_size_mb" in stats


class TestPDFServiceMetadataRetrieval:
    """Test PDF metadata retrieval functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PDFService(upload_dir="test_uploads")

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.service.upload_dir.exists():
            import shutil

            shutil.rmtree(self.service.upload_dir, ignore_errors=True)

    def test_get_pdf_metadata_success(self, sample_pdf_content):
        """Test successful PDF metadata retrieval."""
        file_id = str(uuid.uuid4())

        from datetime import datetime, timezone

        from backend.app.models.pdf import PDFInfo, PDFMetadata

        metadata = PDFMetadata(
            page_count=5,
            file_size=len(sample_pdf_content),
            title="Test Document",
            author="Test Author",
        )
        pdf_info = PDFInfo(
            file_id=file_id,
            filename="test.pdf",
            file_size=len(sample_pdf_content),
            mime_type="application/pdf",
            upload_time=datetime.now(timezone.utc),
            metadata=metadata,
        )
        self.service._file_metadata[file_id] = pdf_info

        result = self.service.get_pdf_metadata(file_id)

        assert isinstance(result, PDFMetadata)
        assert result.page_count == 5
        assert result.title == "Test Document"
        assert result.author == "Test Author"

    def test_get_pdf_metadata_not_found(self):
        """Test PDF metadata retrieval for non-existent file."""
        with pytest.raises(HTTPException) as exc_info:
            self.service.get_pdf_metadata("nonexistent-id")

        assert exc_info.value.status_code == 404
        assert "File not found" in exc_info.value.detail
