"""PDF upload API endpoints.

This module handles PDF file uploads with validation and processing.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..models.pdf import PDFUploadResponse
from ..services.pdf_service import PDFService
from ..utils.api_logging import APILogger, log_api_call, log_file_operation

router = APIRouter()

# Global service instance variable
_pdf_service = None


def init_pdf_service(service: PDFService) -> None:
    """Initialize the global PDF service instance.

    Args:
        service: The PDFService instance to use for all operations.

    """
    global _pdf_service
    _pdf_service = service


def get_pdf_service() -> PDFService:
    """Get the PDF service instance for dependency injection.

    Returns:
        PDFService: The initialized PDF service instance or a new instance as fallback.

    """
    if _pdf_service is None:
        # Fallback to creating new instance if not initialized
        return PDFService()
    return _pdf_service


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
        result = await pdf_service.upload_pdf(file)

        api_logger.log_processing_success(
            file_id=result.file_id,
            filename=result.filename,
            file_size=result.file_size,
            page_count=result.metadata.page_count if result.metadata else None,
        )

        api_logger.log_response_prepared(
            file_id=result.file_id, response_type=type(result).__name__
        )

        return result

    except Exception as upload_error:
        api_logger.log_processing_error(upload_error, filename=file.filename)
        raise
