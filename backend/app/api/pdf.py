"""PDF file operations API endpoints.

This module provides endpoints for retrieving, viewing, and managing PDF files.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..dependencies import get_pdf_service
from ..models.pdf import PDFMetadata
from ..services.pdf_service import PDFService
from ..utils.api_logging import APILogger, log_api_call
from ..utils.validation import validate_file_id

router = APIRouter()


@router.get("/pdf/{file_id}", response_class=FileResponse)
@log_api_call("pdf_retrieve", log_params=True, log_response=False, log_timing=True)
async def get_pdf_file(
    file_id: str, pdf_service: PDFService = Depends(get_pdf_service)
) -> FileResponse:
    """Retrieve a PDF file by its ID.

    - **file_id**: Unique identifier of the PDF file

    Returns the PDF file for viewing.
    """
    api_logger = APILogger("pdf_retrieve")

    api_logger.log_request_received(file_id=file_id)
    api_logger.log_validation_start()

    # Validate file_id using shared utility
    validate_file_id(file_id, api_logger)

    api_logger.log_validation_success(file_id=file_id)
    api_logger.log_processing_start(file_id=file_id)

    try:
        file_path = pdf_service.get_pdf_path(file_id)

        api_logger.log_processing_success(
            file_id=file_id, file_path=str(file_path), file_exists=file_path.exists()
        )

        response = FileResponse(
            path=str(file_path), media_type="application/pdf", filename=f"{file_id}.pdf"
        )

        api_logger.log_response_prepared(
            file_id=file_id, response_type="FileResponse", media_type="application/pdf"
        )

        return response

    except HTTPException as http_error:
        api_logger.log_processing_error(http_error, file_id=file_id, status_code=http_error.status_code)
        raise
    except Exception as error:
        api_logger.log_processing_error(error, file_id=file_id)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve file: {str(error)}"
        )


@router.get("/metadata/{file_id}", response_model=PDFMetadata)
@log_api_call("pdf_metadata", log_params=True, log_response=True, log_timing=True)
async def get_pdf_metadata(
    file_id: str, pdf_service: PDFService = Depends(get_pdf_service)
) -> PDFMetadata:
    """Get metadata for a PDF file.

    - **file_id**: Unique identifier of the PDF file

    Returns PDF metadata including page count, file size, and document properties.
    """
    api_logger = APILogger("pdf_metadata")

    api_logger.log_request_received(file_id=file_id)
    api_logger.log_validation_start()

    # Validate file_id using shared utility
    validate_file_id(file_id, api_logger)

    api_logger.log_validation_success(file_id=file_id)
    api_logger.log_processing_start(file_id=file_id)

    try:
        metadata = pdf_service.get_pdf_metadata(file_id)

        api_logger.log_processing_success(
            file_id=file_id,
            page_count=metadata.page_count,
            file_size=metadata.file_size,
            has_metadata=True,
        )

        api_logger.log_response_prepared(
            file_id=file_id,
            response_type="PDFMetadata",
            page_count=metadata.page_count,
            file_size=metadata.file_size,
        )

        return metadata

    except HTTPException as http_error:
        api_logger.log_processing_error(http_error, file_id=file_id, status_code=http_error.status_code)
        raise
    except Exception as error:
        api_logger.log_processing_error(error, file_id=file_id)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve metadata: {str(error)}"
        )


@router.delete("/pdf/{file_id}")
@log_api_call("pdf_delete", log_params=True, log_response=True, log_timing=True)
async def delete_pdf_file(
    file_id: str, pdf_service: PDFService = Depends(get_pdf_service)
) -> dict[str, str]:
    """Delete a PDF file.

    - **file_id**: Unique identifier of the PDF file

    Returns confirmation of deletion.
    """
    api_logger = APILogger("pdf_delete")

    api_logger.log_request_received(file_id=file_id)
    api_logger.log_validation_start()

    # Validate file_id using shared utility
    validate_file_id(file_id, api_logger)

    api_logger.log_validation_success(file_id=file_id)
    api_logger.log_processing_start(file_id=file_id, operation="file_deletion")

    try:
        success = pdf_service.delete_pdf(file_id)

        if success:
            api_logger.log_processing_success(file_id=file_id, deletion_successful=True)

            response = {"message": f"File {file_id} deleted successfully"}

            api_logger.log_response_prepared(
                file_id=file_id, response_type="dict", operation_result="success"
            )

            return response
        else:
            api_logger.log_processing_error(
                Exception("Delete operation returned False"),
                file_id=file_id,
                deletion_successful=False,
            )
            raise HTTPException(status_code=500, detail="Failed to delete file")

    except HTTPException as http_error:
        api_logger.log_processing_error(http_error, file_id=file_id, status_code=http_error.status_code)
        raise
    except Exception as error:
        api_logger.log_processing_error(error, file_id=file_id)
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(error)}")
