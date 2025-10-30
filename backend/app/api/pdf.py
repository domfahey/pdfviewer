"""PDF file operations API endpoints.

This module provides endpoints for retrieving, viewing, and managing PDF files.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..dependencies import get_pdf_service
from ..models.pdf import PDFMetadata
from ..services.pdf_service import PDFService
from ..utils.api_logging import log_api_call
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
    # Validate file_id using shared utility
    validate_file_id(file_id)

    try:
        file_path = pdf_service.get_pdf_path(file_id)
        return FileResponse(
            path=str(file_path), media_type="application/pdf", filename=f"{file_id}.pdf"
        )
    except HTTPException:
        raise
    except Exception as error:
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
    # Validate file_id using shared utility
    validate_file_id(file_id)

    try:
        return pdf_service.get_pdf_metadata(file_id)
    except HTTPException:
        raise
    except Exception as error:
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
    # Validate file_id using shared utility
    validate_file_id(file_id)

    try:
        success = pdf_service.delete_pdf(file_id)
        if success:
            return {"message": f"File {file_id} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(error)}")
