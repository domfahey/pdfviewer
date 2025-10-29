"""PDF upload API endpoints.

This module handles PDF file uploads with validation and processing.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..dependencies import get_pdf_service
from ..models.pdf import PDFUploadResponse
from ..services.pdf_service import PDFService
from ..utils.api_logging import APILogger, log_api_call, log_file_operation

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
    # Initialize API logger for detailed operation logging
    api_logger = APILogger("pdf_upload")

    # Log request received
    api_logger.log_request_received(
        filename=file.filename,
        content_type=file.content_type,
        size=getattr(file, "size", "unknown"),
    )

    # Validation phase
    api_logger.log_validation_start()

    if not file:
        api_logger.log_validation_error("No file provided")
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename or file.filename.strip() == "":
        api_logger.log_validation_error("No filename provided", filename=file.filename)
        raise HTTPException(status_code=400, detail="No filename provided")

    api_logger.log_validation_success(filename=file.filename)

    # Processing phase
    api_logger.log_processing_start(filename=file.filename)

    try:
        upload_response = await pdf_service.upload_pdf(file)

        api_logger.log_processing_success(
            file_id=upload_response.file_id,
            filename=upload_response.filename,
            file_size=upload_response.file_size,
            page_count=upload_response.metadata.page_count if upload_response.metadata else None,
        )

        api_logger.log_response_prepared(
            file_id=upload_response.file_id, response_type=type(upload_response).__name__
        )

        return upload_response

    except Exception as upload_error:
        api_logger.log_processing_error(upload_error, filename=file.filename)
        raise
