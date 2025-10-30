"""API endpoint for loading PDFs from URLs."""

import io
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, Field, HttpUrl

from ..dependencies import get_pdf_service
from ..models.pdf import PDFUploadResponse
from ..services.pdf_service import PDFService
from ..utils.api_logging import log_api_call
from ..utils.content_disposition import (
    extract_filename_from_url,
    parse_content_disposition,
)
from ..utils.http_client import fetch_with_retry
from ..utils.validation import handle_api_errors

router = APIRouter()


class LoadPDFRequest(BaseModel):
    """Request model for loading PDF from URL."""

    url: Annotated[HttpUrl, Field(description="URL of the PDF to load")]

    model_config = {
        "json_schema_extra": {"example": {"url": "https://example.com/sample.pdf"}}
    }


@router.post("/load-url", response_model=PDFUploadResponse)
@log_api_call("pdf_load_url", log_params=True, log_response=True, log_timing=True)
async def load_pdf_from_url(
    request: LoadPDFRequest,
    pdf_service: PDFService = Depends(get_pdf_service),
) -> PDFUploadResponse:
    """Load a PDF file from a URL for viewing.

    - **url**: URL of the PDF to load

    Returns file ID and metadata for the loaded PDF.
    """
    with handle_api_errors("load PDF from URL"):
        # Download the PDF from the URL with automatic retries
        response = await fetch_with_retry(str(request.url))

        # Check content type
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("application/pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"URL does not point to a PDF file (content-type: {content_type})",
            )

        # Get filename from Content-Disposition header or URL
        # Uses RFC 6266 compliant parser with RFC 5987 support and filename sanitization
        if "content-disposition" in response.headers:
            filename = parse_content_disposition(
                response.headers["content-disposition"], fallback="downloaded.pdf"
            )
        else:
            # Extract and sanitize filename from URL
            filename = extract_filename_from_url(str(request.url), fallback="downloaded.pdf")

        # Create UploadFile from downloaded content
        file = UploadFile(
            filename=filename,
            file=io.BytesIO(response.content),
        )

        # Use the existing PDF service to process the file
        upload_response = await pdf_service.upload_pdf(file)

        return upload_response
