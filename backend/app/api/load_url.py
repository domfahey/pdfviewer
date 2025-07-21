"""API endpoint for loading PDFs from URLs."""

import asyncio
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from ..models.pdf import PDFUploadResponse
from ..services.pdf_service import PDFService
from ..utils.api_logging import log_api_call

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
        from ..services.pdf_service import PDFService

        return PDFService()
    return _pdf_service


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
    """
    Load a PDF file from a URL for viewing.

    - **url**: URL of the PDF to load

    Returns file ID and metadata for the loaded PDF.
    """
    try:
        # Download the PDF from the URL with retries
        timeout = httpx.Timeout(60.0, connect=10.0)
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

        async with httpx.AsyncClient(
            timeout=timeout, limits=limits, follow_redirects=True
        ) as client:
            # Add retry logic for transient failures
            max_retries = 3
            last_error = None

            for attempt in range(max_retries):
                try:
                    response = await client.get(str(request.url))
                    response.raise_for_status()
                    break
                except (httpx.TimeoutException, httpx.NetworkError) as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        await asyncio.sleep(2**attempt)
                        continue
                    raise HTTPException(
                        status_code=504,
                        detail=f"Timeout downloading PDF after {max_retries} attempts: {str(e)}",
                    )
            else:
                if last_error:
                    raise last_error
                else:
                    raise HTTPException(
                        status_code=502,
                        detail="Failed to download PDF after all retries",
                    )

            # Check content type
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("application/pdf"):
                raise HTTPException(
                    status_code=400,
                    detail=f"URL does not point to a PDF file (content-type: {content_type})",
                )

            # Get filename from URL or content-disposition
            filename = "downloaded.pdf"
            if "content-disposition" in response.headers:
                import re

                matches = re.findall(
                    r'filename="?([^"]+)"?', response.headers["content-disposition"]
                )
                if matches:
                    filename = matches[0]
            else:
                # Extract from URL
                url_parts = str(request.url).split("/")
                if url_parts[-1].endswith(".pdf"):
                    filename = url_parts[-1]

            # Create a temporary file-like object
            import io

            from fastapi import UploadFile

            # Create UploadFile from downloaded content
            file = UploadFile(
                filename=filename,
                file=io.BytesIO(response.content),
            )

            # Use the existing PDF service to process the file
            result = await pdf_service.upload_pdf(file)

            return result

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to download PDF from URL: {e.response.status_code}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502, detail=f"Failed to connect to URL: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load PDF from URL: {str(e)}"
        )
