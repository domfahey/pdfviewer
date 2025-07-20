from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class PDFMetadata(BaseModel):
    """PDF metadata model"""

    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    page_count: int = Field(..., gt=0, description="Number of pages in the PDF")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    encrypted: bool = False


class PDFUploadResponse(BaseModel):
    """PDF upload response model"""

    file_id: str = Field(..., description="Unique identifier for the uploaded file")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the file")
    upload_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[PDFMetadata] = None


class PDFInfo(BaseModel):
    """PDF information model"""

    file_id: str
    filename: str
    file_size: int
    mime_type: str
    upload_time: datetime
    metadata: PDFMetadata


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = None
    error_code: Optional[str] = None
