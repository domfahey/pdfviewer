import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.pdf import PDFInfo, PDFMetadata


@pytest.fixture
def client():
    """Test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    # This is a minimal valid PDF file content
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
175
%%EOF"""


@pytest.fixture
def sample_pdf_file(temp_dir, sample_pdf_content):
    """Sample PDF file for testing."""
    pdf_file = temp_dir / "test.pdf"
    pdf_file.write_bytes(sample_pdf_content)
    return pdf_file


@pytest.fixture
def non_pdf_file(temp_dir):
    """Non-PDF file for testing validation."""
    txt_file = temp_dir / "test.txt"
    txt_file.write_text("This is not a PDF file")
    return txt_file


@pytest.fixture
def create_pdf_info():
    """Factory fixture for creating PDFInfo objects."""

    def _create_pdf_info(
        file_id: str | None = None,
        filename: str = "test.pdf",
        file_size: int = 1000,
        page_count: int = 1,
    ) -> PDFInfo:
        """Create a PDFInfo object with default or custom values."""
        import uuid

        file_id = file_id or str(uuid.uuid4())
        metadata = PDFMetadata(page_count=page_count, file_size=file_size)
        return PDFInfo(
            file_id=file_id,
            filename=filename,
            file_size=file_size,
            mime_type="application/pdf",
            upload_time=datetime.now(UTC),
            metadata=metadata,
        )

    return _create_pdf_info


@pytest.fixture
def epa_sample_pdf_url():
    """EPA sample PDF URL for testing with real PDF documents."""
    return "https://19january2021snapshot.epa.gov/sites/static/files/2016-02/documents/epa_sample_letter_sent_to_commissioners_dated_february_29_2015.pdf"


@pytest.fixture
def epa_sample_pdf_content(epa_sample_pdf_url):
    """Download EPA sample PDF content for testing."""
    try:
        response = requests.get(epa_sample_pdf_url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        pytest.skip(f"Could not download EPA sample PDF: {e}")


@pytest.fixture
def epa_sample_pdf_file(temp_dir, epa_sample_pdf_content):
    """EPA sample PDF file for testing."""
    pdf_file = temp_dir / "epa_sample.pdf"
    pdf_file.write_bytes(epa_sample_pdf_content)
    return pdf_file


@pytest.fixture
def weblite_sample_pdf_url():
    """Weblite OCR sample PDF URL for testing with scanned PDF documents."""
    return "https://solutions.weblite.ca/pdfocrx/scansmpl.pdf"


@pytest.fixture
def weblite_sample_pdf_content(weblite_sample_pdf_url):
    """Download Weblite OCR sample PDF content for testing."""
    try:
        response = requests.get(weblite_sample_pdf_url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        pytest.skip(f"Could not download Weblite sample PDF: {e}")


@pytest.fixture
def weblite_sample_pdf_file(temp_dir, weblite_sample_pdf_content):
    """Weblite OCR sample PDF file for testing."""
    pdf_file = temp_dir / "weblite_sample.pdf"
    pdf_file.write_bytes(weblite_sample_pdf_content)
    return pdf_file


@pytest.fixture
def princexml_sample_pdf_url():
    """PrinceXML large essay PDF URL for testing with larger PDF documents."""
    return "https://www.princexml.com/samples/essay.pdf"


@pytest.fixture
def princexml_sample_pdf_content(princexml_sample_pdf_url):
    """Download PrinceXML large essay PDF content for testing."""
    try:
        response = requests.get(
            princexml_sample_pdf_url, timeout=60
        )  # Longer timeout for large file
        response.raise_for_status()
        return response.content
    except Exception as e:
        pytest.skip(f"Could not download PrinceXML sample PDF: {e}")


@pytest.fixture
def princexml_sample_pdf_file(temp_dir, princexml_sample_pdf_content):
    """PrinceXML large essay PDF file for testing."""
    pdf_file = temp_dir / "princexml_essay.pdf"
    pdf_file.write_bytes(princexml_sample_pdf_content)
    return pdf_file


@pytest.fixture
def anyline_sample_pdf_url():
    """Anyline sample scan book PDF URL for testing with complex images and barcodes."""
    return "https://anyline.com/app/uploads/2022/03/anyline-sample-scan-book.pdf"


@pytest.fixture
def anyline_sample_pdf_content(anyline_sample_pdf_url):
    """Download Anyline sample scan book PDF content for testing."""
    try:
        response = requests.get(
            anyline_sample_pdf_url, timeout=60
        )  # Longer timeout for potentially large file
        response.raise_for_status()
        return response.content
    except Exception as e:
        pytest.skip(f"Could not download Anyline sample PDF: {e}")


@pytest.fixture
def anyline_sample_pdf_file(temp_dir, anyline_sample_pdf_content):
    """Anyline sample scan book PDF file for testing."""
    pdf_file = temp_dir / "anyline_sample.pdf"
    pdf_file.write_bytes(anyline_sample_pdf_content)
    return pdf_file


@pytest.fixture
def nhtsa_form_pdf_url():
    """NHTSA PDF form sample URL for testing with form fields and structured layouts."""
    return "https://www.nhtsa.gov/sites/nhtsa.gov/files/documents/mo_par_rev01_2012.pdf"


@pytest.fixture
def nhtsa_form_pdf_content(nhtsa_form_pdf_url):
    """Download NHTSA PDF form content for testing."""
    try:
        response = requests.get(
            nhtsa_form_pdf_url, timeout=60
        )  # Longer timeout for potentially large file
        response.raise_for_status()
        return response.content
    except Exception as e:
        pytest.skip(f"Could not download NHTSA form PDF: {e}")


@pytest.fixture
def nhtsa_form_pdf_file(temp_dir, nhtsa_form_pdf_content):
    """NHTSA PDF form file for testing."""
    pdf_file = temp_dir / "nhtsa_form.pdf"
    pdf_file.write_bytes(nhtsa_form_pdf_content)
    return pdf_file


# Test Helper Functions for Reducing Code Duplication


def create_upload_files(
    filename: str, content: bytes, mime_type: str = "application/pdf"
) -> dict:
    """Create a files dictionary for PDF upload testing.

    Args:
        filename: Name of the file to upload
        content: Binary content of the file
        mime_type: MIME type of the file (default: "application/pdf")

    Returns:
        Dictionary formatted for FastAPI TestClient file upload

    Example:
        files = create_upload_files("test.pdf", pdf_content)
        response = client.post("/api/upload", files=files)
    """
    import io

    return {"file": (filename, io.BytesIO(content), mime_type)}


def assert_upload_response(response, expected_filename: str | None = None):
    """Assert that an upload response has the expected structure and fields.

    Args:
        response: TestClient response object
        expected_filename: Optional expected filename to validate

    Raises:
        AssertionError: If response doesn't match expected structure
    """
    assert response.status_code == 200
    data = response.json()

    # Check core fields
    assert "file_id" in data
    assert "filename" in data
    assert "file_size" in data
    assert "mime_type" in data
    assert "upload_time" in data
    assert "metadata" in data

    if expected_filename:
        assert data["filename"] == expected_filename

    assert data["mime_type"] == "application/pdf"
    assert data["file_size"] > 0

    # Check Pydantic v2 enhanced response fields
    assert "file_size_mb" in data
    assert "upload_time" in data
    assert "upload_age_hours" in data
    assert "upload_status" in data
    assert "processing_priority" in data
    assert "_poc_info" in data


def assert_metadata_fields(metadata: dict, min_pages: int = 1):
    """Assert that metadata has expected fields and valid values.

    Args:
        metadata: Metadata dictionary from upload response
        min_pages: Minimum expected page count (default: 1)

    Raises:
        AssertionError: If metadata doesn't have expected structure
    """
    # Check essential metadata fields
    assert "page_count" in metadata
    assert "file_size" in metadata
    assert "encrypted" in metadata

    # Check computed fields
    assert "file_size_mb" in metadata
    assert "document_complexity_score" in metadata
    assert "document_category" in metadata
    assert "is_large_document" in metadata

    # Validate values
    assert metadata["page_count"] >= min_pages
    assert metadata["file_size"] > 0
    assert isinstance(metadata["encrypted"], bool)


def perform_full_pdf_workflow(
    client: TestClient, filename: str, content: bytes
) -> tuple[str, dict]:
    """Perform a complete PDF workflow: upload, retrieve, get metadata, delete.

    Args:
        client: FastAPI TestClient instance
        filename: Name of the PDF file
        content: Binary content of the PDF file

    Returns:
        Tuple of (file_id, upload_data)

    Raises:
        AssertionError: If any step in the workflow fails
    """
    import io

    # Step 1: Upload PDF
    files = create_upload_files(filename, content)
    upload_response = client.post("/api/upload", files=files)
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    file_id = upload_data["file_id"]

    # Step 2: Get PDF file
    pdf_response = client.get(f"/api/pdf/{file_id}")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert len(pdf_response.content) > 0

    # Step 3: Get metadata
    metadata_response = client.get(f"/api/metadata/{file_id}")
    assert metadata_response.status_code == 200
    metadata = metadata_response.json()
    assert_metadata_fields(metadata)

    # Step 4: Delete PDF
    delete_response = client.delete(f"/api/pdf/{file_id}")
    assert delete_response.status_code == 200
    delete_data = delete_response.json()
    assert "deleted successfully" in delete_data["message"]

    # Step 5: Verify file is deleted
    pdf_response_after_delete = client.get(f"/api/pdf/{file_id}")
    assert pdf_response_after_delete.status_code == 404

    return file_id, upload_data


def assert_error_response(response, expected_status: int, error_substring: str = ""):
    """Assert that an error response has the expected status and message.

    Args:
        response: TestClient response object
        expected_status: Expected HTTP status code
        error_substring: Optional substring to check in error detail (case-insensitive)

    Raises:
        AssertionError: If response doesn't match expected error format
    """
    assert response.status_code == expected_status
    data = response.json()
    assert "detail" in data

    if error_substring:
        assert error_substring.lower() in data["detail"].lower()
