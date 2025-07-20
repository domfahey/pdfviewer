from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..models.pdf import PDFMetadata
from ..services.pdf_service import PDFService

router = APIRouter()

# Global service instance variable
_pdf_service = None


def init_pdf_service(service: PDFService) -> None:
    global _pdf_service
    _pdf_service = service


# Dependency to get PDF service
def get_pdf_service() -> PDFService:
    if _pdf_service is None:
        # Fallback to creating new instance if not initialized
        return PDFService()
    return _pdf_service


@router.get("/pdf/{file_id}", response_class=FileResponse)
async def get_pdf_file(
    file_id: str, pdf_service: PDFService = Depends(get_pdf_service)
) -> FileResponse:
    """
    Retrieve a PDF file by its ID.

    - **file_id**: Unique identifier of the PDF file

    Returns the PDF file for viewing.
    """
    try:
        file_path = pdf_service.get_pdf_path(file_id)
        return FileResponse(
            path=str(file_path), media_type="application/pdf", filename=f"{file_id}.pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve file: {str(e)}"
        )


@router.get("/metadata/{file_id}", response_model=PDFMetadata)
async def get_pdf_metadata(
    file_id: str, pdf_service: PDFService = Depends(get_pdf_service)
) -> PDFMetadata:
    """
    Get metadata for a PDF file.

    - **file_id**: Unique identifier of the PDF file

    Returns PDF metadata including page count, file size, and document properties.
    """
    return pdf_service.get_pdf_metadata(file_id)


@router.delete("/pdf/{file_id}")
async def delete_pdf_file(
    file_id: str, pdf_service: PDFService = Depends(get_pdf_service)
) -> dict[str, str]:
    """
    Delete a PDF file.

    - **file_id**: Unique identifier of the PDF file

    Returns confirmation of deletion.
    """
    success = pdf_service.delete_pdf(file_id)
    if success:
        return {"message": f"File {file_id} deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete file")
