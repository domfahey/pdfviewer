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
