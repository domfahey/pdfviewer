"""PDF upload API endpoints.

This module handles PDF file uploads with validation and processing.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..dependencies import get_pdf_service
from ..models.pdf import PDFUploadResponse
from ..services.pdf_service import PDFService
from ..utils.api_logging import log_api_call, log_file_operation

router = APIRouter()


@router.post("/upload", response_model=PDFUploadResponse)
@log_file_operation("pdf_upload", file_param="file", log_file_details=True)
@log_api_call("pdf_upload", log_params=True, log_response=True, log_timing=True)
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload"),
    pdf_service: PDFService = Depends(get_pdf_service),
) -> PDFUploadResponse:
    """Upload a PDF file for viewing.

    - **file**: PDF file to upload (max 50MB)

    Returns file ID and metadata for the uploaded PDF.
    """
    # Basic validation
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename or file.filename.strip() == "":
        raise HTTPException(status_code=400, detail="No filename provided")

    return await pdf_service.upload_pdf(file)
