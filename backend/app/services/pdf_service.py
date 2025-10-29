"""PDF processing service for file operations and metadata extraction.

This module provides comprehensive PDF handling including upload,
validation, metadata extraction, and file management.
"""

import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import aiofiles
import magic
from fastapi import HTTPException, UploadFile
from pypdf import PdfReader

from ..core.logging import get_logger, log_performance
from ..models.pdf import PDFInfo, PDFMetadata, PDFUploadResponse
from ..utils.logger import (
    FileOperationLogger,
    PerformanceTracker,
    log_exception_context,
)


class PDFService:
    """Service for handling PDF operations with comprehensive logging."""

    def __init__(self, upload_dir: str = "uploads"):
        """Initialize the PDF service.

        Args:
            upload_dir: Directory path for storing uploaded PDF files. Defaults to "uploads".

        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_mime_types = {"application/pdf"}

        # In-memory storage for file metadata (use database in production)
        self._file_metadata: dict[str, PDFInfo] = {}

        # Initialize loggers
        self.logger = get_logger(__name__)
        self.file_logger = FileOperationLogger(self.logger)

        self.logger.info(
            "PDF service initialized",
            upload_dir=str(self.upload_dir),
            max_file_size_mb=self.max_file_size / (1024 * 1024),
            allowed_mime_types=list(self.allowed_mime_types),
        )

    def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file with detailed logging."""
        validation_context = {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": file.size,
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

        if file.size and file.size > self.max_file_size:
            self.logger.warning(
                "File validation failed: file too large",
                **validation_context,
                max_file_size_mb=self.max_file_size / (1024 * 1024),
                file_size_mb=file.size / (1024 * 1024) if file.size else 0,
            )
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File too large. Maximum size is "
                    f"{self.max_file_size / (1024 * 1024):.1f}MB"
                ),
            )

        self.logger.debug("File validation passed", **validation_context)

    def _get_pdf_attr(self, pdf_info, attr: str):
        """Helper to safely get PDF info attributes."""
        return getattr(pdf_info, attr, None) if pdf_info else None

    @log_performance("PDF metadata extraction")
    def _extract_pdf_metadata(self, file_path: Path) -> PDFMetadata:
        """Extract metadata from PDF file with comprehensive logging."""
        with PerformanceTracker(
            "PDF metadata extraction",
            self.logger,
            file_path=str(file_path),
            file_size_bytes=file_path.stat().st_size,
        ):
            try:
                with open(file_path, "rb") as pdf_file:
                    reader = PdfReader(pdf_file)
                    page_count = len(reader.pages)
                    file_size = file_path.stat().st_size
                    encrypted = reader.is_encrypted
                    pdf_info = reader.metadata

                    # Create metadata with validation
                    try:
                        metadata = PDFMetadata(
                            title=self._get_pdf_attr(pdf_info, "title"),
                            author=self._get_pdf_attr(pdf_info, "author"),
                            subject=self._get_pdf_attr(pdf_info, "subject"),
                            creator=self._get_pdf_attr(pdf_info, "creator"),
                            producer=self._get_pdf_attr(pdf_info, "producer"),
                            creation_date=self._get_pdf_attr(pdf_info, "creation_date"),
                            modification_date=self._get_pdf_attr(pdf_info, "modification_date"),
                            page_count=page_count,
                            file_size=file_size,
                            encrypted=encrypted,
                        )
                    except Exception as metadata_error:
                        self.logger.warning(
                            "PDF metadata validation failed, using fallback",
                            file_path=str(file_path),
                            metadata_error=str(metadata_error),
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

            except Exception as extraction_error:
                # Log the specific error and return fallback metadata
                log_exception_context(
                    self.logger,
                    "PDF metadata extraction",
                    extraction_error,
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
        # Start timing the entire upload operation
        with PerformanceTracker(
            "PDF file upload",
            self.logger,
            filename=file.filename,
            file_size=file.size,
        ) as upload_tracker:
            # Log upload start
            self.file_logger.upload_started(
                file.filename or "unknown",
                file.size or 0,
                content_type=file.content_type,
            )

            self._validate_file(file)

            # Generate unique file ID and file path
            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix  # type: ignore[arg-type]
            stored_filename = f"{file_id}{file_extension}"
            file_path = self.upload_dir / stored_filename

            self.logger.info(
                "Processing file upload",
                file_id=file_id,
                original_filename=file.filename,
                stored_filename=stored_filename,
                target_path=str(file_path),
            )

            try:
                # Save file
                with PerformanceTracker(
                    "File write operation",
                    self.logger,
                    file_id=file_id,
                    file_size=file.size,
                ):
                    async with aiofiles.open(file_path, "wb") as pdf_file:
                        content = await file.read()
                        await pdf_file.write(content)

                # Verify MIME type
                with PerformanceTracker(
                    "MIME type verification", self.logger, file_id=file_id
                ):
                    mime_type = magic.from_file(str(file_path), mime=True)

                if mime_type not in self.allowed_mime_types:
                    self.logger.warning(
                        "Invalid MIME type detected, removing file",
                        file_id=file_id,
                        detected_mime_type=mime_type,
                        allowed_mime_types=list(self.allowed_mime_types),
                    )
                    os.unlink(file_path)
                    raise HTTPException(status_code=400, detail="Invalid file type")

                # Extract metadata
                metadata = self._extract_pdf_metadata(file_path)

                # Store file info
                pdf_info = PDFInfo(
                    file_id=file_id,
                    filename=file.filename,
                    file_size=file_path.stat().st_size,
                    mime_type=mime_type,
                    upload_time=datetime.now(UTC),
                    metadata=metadata,
                )
                self._file_metadata[file_id] = pdf_info

                # Log successful completion
                file_size = file_path.stat().st_size
                self.file_logger.upload_completed(
                    file_id,
                    file.filename,
                    upload_tracker.duration_ms or 0,
                    mime_type=mime_type,
                    page_count=metadata.page_count,
                    file_size_mb=round(file_size / (1024 * 1024), 2),
                )

                response = PDFUploadResponse(
                    file_id=file_id,
                    filename=file.filename,
                    file_size=file_path.stat().st_size,
                    mime_type=mime_type,
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
            except Exception as upload_error:
                # Log unexpected errors
                log_exception_context(
                    self.logger,
                    "PDF file upload",
                    upload_error,
                    file_id=file_id,
                    filename=file.filename,
                    file_path=str(file_path),
                )

                self.file_logger.upload_failed(
                    file.filename or "unknown",
                    str(upload_error),
                    upload_tracker.duration_ms or 0,
                    file_id=file_id,
                    error_type=type(upload_error).__name__,
                )

                # Clean up file if something went wrong
                if file_path.exists():
                    try:
                        os.unlink(file_path)
                        self.logger.debug(
                            "Cleaned up failed upload file", file_path=str(file_path)
                        )
                    except Exception as cleanup_error:
                        self.logger.error(
                            "Failed to clean up upload file",
                            file_path=str(file_path),
                            cleanup_error=str(cleanup_error),
                        )

                raise HTTPException(
                    status_code=500, detail=f"Failed to process file: {str(upload_error)}"
                )

    def get_pdf_path(self, file_id: str) -> Path:
        """Get file path for PDF with logging."""
        self.logger.debug("Getting PDF path", file_id=file_id)

        if file_id not in self._file_metadata:
            self.logger.warning("PDF file not found in metadata", file_id=file_id)
            raise HTTPException(status_code=404, detail="File not found")

        # Find file with this ID (assuming .pdf extension)
        file_path = self.upload_dir / f"{file_id}.pdf"
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
            file_path = self.upload_dir / f"{file_id}.pdf"

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

            except Exception as deletion_error:
                # Log deletion failure
                log_exception_context(
                    self.logger,
                    "PDF file deletion",
                    deletion_error,
                    file_id=file_id,
                    file_path=str(file_path),
                )

                self.file_logger.deletion_logged(
                    file_id,
                    success=False,
                    error=str(deletion_error),
                    error_type=type(deletion_error).__name__,
                    duration_ms=delete_tracker.duration_ms,
                )

                raise HTTPException(
                    status_code=500, detail=f"Failed to delete file: {str(deletion_error)}"
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
        total_size = sum(f.file_size for f in files)
        page_counts = [f.metadata.page_count if f.metadata else 0 for f in files]
        total_pages = sum(page_counts)

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
