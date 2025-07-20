import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
import magic
from fastapi import HTTPException, UploadFile
from pypdf import PdfReader

from ..models.pdf import PDFInfo, PDFMetadata, PDFUploadResponse


class PDFService:
    """Service for handling PDF operations"""

    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_mime_types = {"application/pdf"}

        # In-memory storage for file metadata (use database in production)
        self._file_metadata: dict[str, PDFInfo] = {}

    def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        if file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {self.max_file_size / (1024 * 1024):.1f}MB",
            )

    def _extract_pdf_metadata(self, file_path: Path) -> PDFMetadata:
        """Extract metadata from PDF file"""
        try:
            with open(file_path, "rb") as f:
                reader = PdfReader(f)

                # Get basic info
                page_count = len(reader.pages)
                file_size = file_path.stat().st_size
                encrypted = reader.is_encrypted

                # Get document info
                info = reader.metadata
                metadata = PDFMetadata(
                    title=getattr(info, "title", None) if info else None,
                    author=getattr(info, "author", None) if info else None,
                    subject=getattr(info, "subject", None) if info else None,
                    creator=getattr(info, "creator", None) if info else None,
                    producer=getattr(info, "producer", None) if info else None,
                    creation_date=(
                        getattr(info, "creation_date", None) if info else None
                    ),
                    modification_date=(
                        getattr(info, "modification_date", None) if info else None
                    ),
                    page_count=page_count,
                    file_size=file_size,
                    encrypted=encrypted,
                )

                return metadata

        except Exception:
            # Return basic metadata if extraction fails
            return PDFMetadata(
                page_count=1,  # Default fallback
                file_size=file_path.stat().st_size,
                encrypted=False,
            )

    async def upload_pdf(self, file: UploadFile) -> PDFUploadResponse:
        """Upload and process PDF file"""
        self._validate_file(file)

        # Generate unique file ID
        file_id = str(uuid.uuid4())
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        file_extension = Path(file.filename).suffix
        stored_filename = f"{file_id}{file_extension}"
        file_path = self.upload_dir / stored_filename

        try:
            # Save file
            async with aiofiles.open(file_path, "wb") as f:
                content = await file.read()
                await f.write(content)

            # Verify MIME type
            mime_type = magic.from_file(str(file_path), mime=True)
            if mime_type not in self.allowed_mime_types:
                os.unlink(file_path)  # Remove invalid file
                raise HTTPException(status_code=400, detail="Invalid file type")

            # Extract metadata
            metadata = self._extract_pdf_metadata(file_path)

            # Store file info
            pdf_info = PDFInfo(
                file_id=file_id,
                filename=file.filename,
                file_size=file_path.stat().st_size,
                mime_type=mime_type,
                upload_time=datetime.now(timezone.utc),
                metadata=metadata,
            )
            self._file_metadata[file_id] = pdf_info

            return PDFUploadResponse(
                file_id=file_id,
                filename=file.filename,
                file_size=file_path.stat().st_size,
                mime_type=mime_type,
                metadata=metadata,
            )

        except Exception as e:
            # Clean up file if something went wrong
            if file_path.exists():
                os.unlink(file_path)
            raise HTTPException(
                status_code=500, detail=f"Failed to process file: {str(e)}"
            )

    def get_pdf_path(self, file_id: str) -> Path:
        """Get file path for PDF"""
        if file_id not in self._file_metadata:
            raise HTTPException(status_code=404, detail="File not found")

        # Find file with this ID (assuming .pdf extension)
        file_path = self.upload_dir / f"{file_id}.pdf"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")

        return file_path

    def get_pdf_metadata(self, file_id: str) -> PDFMetadata:
        """Get PDF metadata"""
        if file_id not in self._file_metadata:
            raise HTTPException(status_code=404, detail="File not found")

        return self._file_metadata[file_id].metadata

    def delete_pdf(self, file_id: str) -> bool:
        """Delete PDF file"""
        if file_id not in self._file_metadata:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = self.upload_dir / f"{file_id}.pdf"
        try:
            if file_path.exists():
                os.unlink(file_path)
            del self._file_metadata[file_id]
            return True
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to delete file: {str(e)}"
            )

    def list_files(self) -> dict[str, PDFInfo]:
        """List all uploaded files"""
        return self._file_metadata.copy()
