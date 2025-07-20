from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..models.pdf import PDFUploadResponse
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


@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload"),
    pdf_service: PDFService = Depends(get_pdf_service),
) -> PDFUploadResponse:
    """
    Upload a PDF file for viewing.

    - **file**: PDF file to upload (max 50MB)

    Returns file ID and metadata for the uploaded PDF.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename or file.filename.strip() == "":
        raise HTTPException(status_code=400, detail="No filename provided")

    return await pdf_service.upload_pdf(file)
