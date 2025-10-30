"""PDF processing service for file operations and metadata extraction.

This module provides comprehensive PDF handling including upload,
validation, metadata extraction, and file management.
"""

import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile
from pypdf import PdfReader

from ..core.logging import get_logger
from ..models.pdf import PDFInfo, PDFMetadata, PDFUploadResponse
from ..utils.decorators import performance_logger as log_performance
from ..utils.logger import (
    FileOperationLogger,
    PerformanceTracker,
    log_exception_context,
)


class PDFService:
    """Service for handling PDF operations with comprehensive logging."""

    # Configuration constants
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks for file upload streaming

    def __init__(self, upload_dir: str = "uploads"):
        """Initialize the PDF service.

        Args:
            upload_dir: Directory path for storing uploaded PDF files. Defaults to "uploads".

        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.max_file_size = 50 * 1024 * 1024  # 50MB

        # In-memory storage for file metadata (use database in production)
        self._file_metadata: dict[str, PDFInfo] = {}
        self._stored_files: dict[str, str] = {}

        # Initialize loggers
        self.logger = get_logger(__name__)
        self.file_logger = FileOperationLogger(self.logger)

        self.logger.info(
            "PDF service initialized",
            upload_dir=str(self.upload_dir),
            max_file_size_mb=self.max_file_size / (1024 * 1024),
        )

    def _determine_upload_size(self, file: UploadFile) -> int | None:
        """Best-effort size calculation without relying on UploadFile.size."""
        file_obj = getattr(file, "file", None)
        if file_obj and hasattr(file_obj, "tell") and hasattr(file_obj, "seek"):
            try:
                current_pos = file_obj.tell()
                file_obj.seek(0, os.SEEK_END)
                size = file_obj.tell()
                file_obj.seek(current_pos)
                return size
            except (OSError, ValueError):
                return None
        return None

    def _validate_file(self, file: UploadFile, file_size: int | None) -> None:
        """Validate uploaded file with detailed logging."""
        validation_context = {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": file_size,
        }

        self.logger.debug("Starting file validation", **validation_context)

        if not file.filename:
            self.logger.warning(
                "File validation failed: no filename provided", **validation_context
            )
            raise HTTPException(status_code=400, detail="No filename provided")

        if not file.filename.lower().endswith(".pdf"):
            self.logger.warning(
                "File validation failed: invalid file extension",
                **validation_context,
                expected_extension=".pdf",
            )
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        if file_size and file_size > self.max_file_size:
            self.logger.warning(
                "File validation failed: file too large",
                **validation_context,
                max_file_size_mb=self.max_file_size / (1024 * 1024),
                file_size_mb=file_size / (1024 * 1024),
            )
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File too large. Maximum size is "
                    f"{self.max_file_size / (1024 * 1024):.1f}MB"
                ),
            )

        self.logger.debug("File validation passed", **validation_context)

    def _get_pdf_attr(self, pdf_info: PDFInfo | None, attr: str) -> str | None:
        """Helper to safely get PDF info attributes."""
        return getattr(pdf_info, attr, None) if pdf_info else None

    def _validate_pdf_header(self, file_path: Path) -> bool:
        """Validate that file has a valid PDF header.
        
        PDF files must start with "%PDF-" followed by version number.
        This is a lightweight alternative to libmagic for basic PDF validation.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file has valid PDF header, False otherwise
        """
        try:
            with open(file_path, "rb") as f:
                header = f.read(8)
                # PDF files start with "%PDF-" (bytes 0x25 0x50 0x44 0x46 0x2D)
                # followed by version like "1.4" or "1.7"
                return header.startswith(b"%PDF-")
        except Exception as e:
            self.logger.warning(
                "Failed to read file header",
                file_path=str(file_path),
                error=str(e),
            )
            return False

    @log_performance("PDF metadata extraction")
    def _extract_pdf_metadata(self, file_path: Path) -> PDFMetadata:
        """Extract metadata from PDF file with comprehensive logging."""
        # Cache file.stat() result to avoid duplicate filesystem call
        file_stat = file_path.stat()

        with PerformanceTracker(
            "PDF metadata extraction",
            self.logger,
            file_path=str(file_path),
            file_size_bytes=file_stat.st_size,
        ):
            try:
                with open(file_path, "rb") as pdf_binary_file:
                    reader = PdfReader(pdf_binary_file)

                    # Get basic info
                    page_count = len(reader.pages)
                    file_size = file_stat.st_size  # Use cached stat result
                    encrypted = reader.is_encrypted

                    # Get document info
                    document_info = reader.metadata

                    # Extract metadata attributes once to avoid repeated getattr calls
                    if document_info:
                        title = getattr(document_info, "title", None)
                        author = getattr(document_info, "author", None)
                        subject = getattr(document_info, "subject", None)
                        creator = getattr(document_info, "creator", None)
                        producer = getattr(document_info, "producer", None)
                        creation_date = getattr(document_info, "creation_date", None)
                        modification_date = getattr(
                            document_info, "modification_date", None
                        )
                    else:
                        title = author = subject = creator = producer = None
                        creation_date = modification_date = None

                    # Log metadata extraction details
                    self.logger.debug(
                        "PDF metadata extracted",
                        page_count=page_count,
                        file_size_mb=round(file_size / (1024 * 1024), 2),
                        encrypted=encrypted,
                        has_metadata=document_info is not None,
                        title=title,
                        author=author,
                    )

                    # Create metadata with enhanced validation
                    try:
                        metadata = PDFMetadata(
                            title=title,
                            author=author,
                            subject=subject,
                            creator=creator,
                            producer=producer,
                            creation_date=creation_date,
                            modification_date=modification_date,
                            page_count=page_count,
                            file_size=file_size,
                            encrypted=encrypted,
                        )
                    except Exception as metadata_exception:
                        self.logger.warning(
                            "PDF metadata validation failed, using fallback",
                            file_path=str(file_path),
                            metadata_error=str(metadata_exception),
                            page_count=page_count,
                            file_size=file_size,
                        )
                        # Use minimal fallback metadata
                        metadata = PDFMetadata(
                            page_count=max(1, page_count),  # Ensure positive
                            file_size=file_size,
                            encrypted=False,  # Safe default
                        )

                    return metadata

            except Exception as extraction_exception:
                # Log the specific error and return fallback metadata
                log_exception_context(
                    self.logger,
                    "PDF metadata extraction",
                    extraction_exception,
                    file_path=str(file_path),
                    fallback_used=True,
                )

                # Return basic fallback metadata
                fallback_metadata = PDFMetadata(
                    page_count=1,
                    file_size=max(1, file_path.stat().st_size),
                    encrypted=False,
                )
                self.logger.warning(
                    "Using fallback metadata due to extraction failure",
                    file_path=str(file_path),
                )
                return fallback_metadata

    async def upload_pdf(self, file: UploadFile) -> PDFUploadResponse:
        """Upload and process PDF file with comprehensive logging."""
        expected_file_size = self._determine_upload_size(file)

        # Start timing the entire upload operation
        with PerformanceTracker(
            "PDF file upload",
            self.logger,
            filename=file.filename,
            file_size=expected_file_size,
        ) as upload_tracker:
            # Log upload start
            self.file_logger.upload_started(
                file.filename or "unknown",
                expected_file_size or 0,
                content_type=file.content_type,
            )

            self._validate_file(file, expected_file_size)

            # Generate unique file ID and file path
            # After validation, filename is guaranteed to be non-None
            if file.filename is None:
                raise ValueError("Filename should not be None after validation")
            filename: str = file.filename
            file_id = str(uuid.uuid4())
            file_extension = Path(filename).suffix
            stored_filename = f"{file_id}{file_extension}"
            file_path = self.upload_dir / stored_filename

            self.logger.info(
                "Processing file upload",
                file_id=file_id,
                original_filename=filename,
                stored_filename=stored_filename,
                target_path=str(file_path),
            )

            try:
                # Save file using chunked reading for better memory efficiency
                # This prevents loading entire large PDFs into memory at once
                with PerformanceTracker(
                    "File write operation",
                    self.logger,
                    file_id=file_id,
                    file_size=expected_file_size,
                ):
                    try:
                        await file.seek(0)
                    except Exception:
                        # Some upload backends may not support seek; proceed with current position
                        pass

                    async with aiofiles.open(file_path, "wb") as pdf_file:
                        while True:
                            chunk = await file.read(self.CHUNK_SIZE)
                            if not chunk:
                                break
                            await pdf_file.write(chunk)

                # Cache file.stat() result to avoid multiple filesystem calls
                file_stat = file_path.stat()
                actual_file_size = file_stat.st_size
                self.logger.debug(
                    "File written to disk",
                    file_id=file_id,
                    expected_size=expected_file_size,
                    actual_size=actual_file_size,
                    size_match=(
                        expected_file_size == actual_file_size
                        if expected_file_size is not None
                        else True
                    ),
                )

                # Verify PDF format using lightweight header validation
                # This replaces libmagic dependency and is significantly faster
                with PerformanceTracker(
                    "PDF header verification", self.logger, file_id=file_id
                ):
                    is_valid_pdf = self._validate_pdf_header(file_path)

                if not is_valid_pdf:
                    self.logger.warning(
                        "Invalid PDF format detected, removing file",
                        file_id=file_id,
                    )
                    os.unlink(file_path)
                    raise HTTPException(status_code=400, detail="Invalid PDF file format")

                # Extract metadata
                metadata = self._extract_pdf_metadata(file_path)

                # Store file info (reuse cached file_stat)
                pdf_info = PDFInfo(
                    file_id=file_id,
                    filename=filename,
                    file_size=actual_file_size,
                    mime_type="application/pdf",  # Always PDF after validation
                    upload_time=datetime.now(UTC),
                    metadata=metadata,
                )
                self._file_metadata[file_id] = pdf_info
                self._stored_files[file_id] = stored_filename

                # Log successful completion
                self.file_logger.upload_completed(
                    file_id,
                    filename,
                    upload_tracker.duration_ms or 0,
                    mime_type="application/pdf",
                    page_count=metadata.page_count,
                    file_size_mb=round(actual_file_size / (1024 * 1024), 2),
                )

                response = PDFUploadResponse(
                    file_id=file_id,
                    filename=filename,
                    file_size=actual_file_size,
                    mime_type="application/pdf",
                    upload_time=datetime.now(UTC),
                    metadata=metadata,
                )

                self.logger.info(
                    "PDF upload completed successfully",
                    file_id=file_id,
                    response_data={
                        "file_id": response.file_id,
                        "filename": response.filename,
                        "file_size": response.file_size,
                        "page_count": (
                            response.metadata.page_count if response.metadata else 0
                        ),
                    },
                )

                return response

            except HTTPException:
                # Re-raise HTTP exceptions (these are expected errors)
                raise
            except Exception as upload_exception:
                # Log unexpected errors
                log_exception_context(
                    self.logger,
                    "PDF file upload",
                    upload_exception,
                    file_id=file_id,
                    filename=file.filename,
                    file_path=str(file_path),
                )

                self.file_logger.upload_failed(
                    file.filename or "unknown",
                    str(upload_exception),
                    upload_tracker.duration_ms or 0,
                    file_id=file_id,
                    error_type=type(upload_exception).__name__,
                )

                # Clean up file if something went wrong
                if file_path.exists():
                    try:
                        os.unlink(file_path)
                        self.logger.debug(
                            "Cleaned up failed upload file", file_path=str(file_path)
                        )
                    except Exception as cleanup_exception:
                        self.logger.error(
                            "Failed to clean up upload file",
                            file_path=str(file_path),
                            cleanup_error=str(cleanup_exception),
                        )

                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to process file: {str(upload_exception)}",
                )

    def get_pdf_path(self, file_id: str) -> Path:
        """Get file path for PDF with logging."""
        self.logger.debug("Getting PDF path", file_id=file_id)

        if file_id not in self._file_metadata:
            self.logger.warning("PDF file not found in metadata", file_id=file_id)
            raise HTTPException(status_code=404, detail="File not found")

        stored_filename = self._stored_files.get(file_id)
        if not stored_filename:
            self.logger.error(
                "Stored filename not found for file_id",
                file_id=file_id,
                upload_dir=str(self.upload_dir),
            )
            raise HTTPException(status_code=404, detail="File not found on disk")

        file_path = self.upload_dir / stored_filename
        if not file_path.exists():
            self.logger.error(
                "PDF file not found on disk",
                file_id=file_id,
                expected_path=str(file_path),
                upload_dir=str(self.upload_dir),
            )
            raise HTTPException(status_code=404, detail="File not found on disk")

        self.file_logger.access_logged(file_id, "get_path", file_path=str(file_path))
        return file_path

    def get_pdf_metadata(self, file_id: str) -> PDFMetadata:
        """Get PDF metadata with logging."""
        self.logger.debug("Getting PDF metadata", file_id=file_id)

        if file_id not in self._file_metadata:
            self.logger.warning("PDF metadata not found", file_id=file_id)
            raise HTTPException(status_code=404, detail="File not found")

        metadata = self._file_metadata[file_id].metadata
        self.file_logger.access_logged(
            file_id,
            "get_metadata",
            page_count=metadata.page_count,
            file_size_mb=round(metadata.file_size / (1024 * 1024), 2),
        )

        return metadata

    def delete_pdf(self, file_id: str) -> bool:
        """Delete PDF file with comprehensive logging."""
        with PerformanceTracker(
            "PDF file deletion",
            self.logger,
            file_id=file_id,
        ) as delete_tracker:
            self.logger.info("Starting PDF file deletion", file_id=file_id)

            if file_id not in self._file_metadata:
                self.logger.warning(
                    "Cannot delete PDF: file not found in metadata", file_id=file_id
                )
                raise HTTPException(status_code=404, detail="File not found")

            file_info = self._file_metadata[file_id]
            stored_filename = self._stored_files.get(file_id)
            if not stored_filename:
                self.logger.warning(
                    "Stored filename missing during deletion",
                    file_id=file_id,
                )
                raise HTTPException(status_code=404, detail="File not found on disk")

            file_path = self.upload_dir / stored_filename

            try:
                # Delete physical file
                if file_path.exists():
                    file_size_before = file_path.stat().st_size
                    os.unlink(file_path)
                    self.logger.debug(
                        "Physical file deleted",
                        file_id=file_id,
                        file_path=str(file_path),
                        file_size_mb=round(file_size_before / (1024 * 1024), 2),
                    )
                else:
                    self.logger.warning(
                        "Physical file not found during deletion",
                        file_id=file_id,
                        expected_path=str(file_path),
                    )

                # Remove from metadata
                del self._file_metadata[file_id]
                self._stored_files.pop(file_id, None)

                # Log successful deletion
                self.file_logger.deletion_logged(
                    file_id,
                    success=True,
                    filename=file_info.filename,
                    original_file_size=file_info.file_size,
                    duration_ms=delete_tracker.duration_ms,
                )

                self.logger.info("PDF file deleted successfully", file_id=file_id)
                return True

            except Exception as deletion_exception:
                # Log deletion failure
                log_exception_context(
                    self.logger,
                    "PDF file deletion",
                    deletion_exception,
                    file_id=file_id,
                    file_path=str(file_path),
                )

                self.file_logger.deletion_logged(
                    file_id,
                    success=False,
                    error=str(deletion_exception),
                    error_type=type(deletion_exception).__name__,
                    duration_ms=delete_tracker.duration_ms,
                )

                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to delete file: {str(deletion_exception)}",
                )

    def list_files(self) -> dict[str, PDFInfo]:
        """List all uploaded files with logging."""
        file_count = len(self._file_metadata)
        total_size = sum(info.file_size for info in self._file_metadata.values())

        self.logger.debug(
            "Listing PDF files",
            file_count=file_count,
            total_size_mb=round(total_size / (1024 * 1024), 2),
        )

        self.file_logger.access_logged(
            "all",
            "list_files",
            file_count=file_count,
            total_size_mb=round(total_size / (1024 * 1024), 2),
        )

        return self._file_metadata.copy()

    def get_service_stats(self) -> dict[str, int | float | str]:
        """Get service statistics for monitoring and debugging."""
        files = list(self._file_metadata.values())

        # Use single pass through files for better performance
        total_size = 0
        total_pages = 0
        for f in files:
            total_size += f.file_size
            total_pages += f.metadata.page_count if f.metadata else 0

        stats = {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_pages": total_pages,
            "average_file_size_mb": (
                round((total_size / len(files)) / (1024 * 1024), 2) if files else 0
            ),
            "average_pages_per_file": (
                round(total_pages / len(files), 1) if files else 0
            ),
            "upload_directory": str(self.upload_dir),
            "max_file_size_mb": self.max_file_size / (1024 * 1024),
        }

        self.logger.info("Service statistics requested", **stats)
        return stats
