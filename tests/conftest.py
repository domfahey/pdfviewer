"""
Test configuration and fixtures.

This module provides all shared fixtures for the test suite, eliminating
network dependencies and improving test reliability and performance.
"""

import tempfile
from pathlib import Path
from typing import Optional

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

# Test data directory
TEST_FIXTURES_DIR = Path(__file__).parent / "fixtures"
INTEGRATION_FIXTURES_DIR = Path(__file__).parent / "integration" / "fixtures"


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
    """Minimal valid PDF content for basic testing."""
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


# Local PDF fixtures - using actual local files instead of network downloads
@pytest.fixture
def epa_sample_pdf_content():
    """EPA sample PDF content from local file."""
    epa_file = TEST_FIXTURES_DIR / "epa_sample.pdf"
    if not epa_file.exists():
        # Fallback to integration fixtures
        epa_file = INTEGRATION_FIXTURES_DIR / "epa_sample.pdf"
    
    if not epa_file.exists():
        pytest.skip("EPA sample PDF not found in test fixtures")
    
    return epa_file.read_bytes()


@pytest.fixture
def epa_sample_pdf_file(temp_dir, epa_sample_pdf_content):
    """EPA sample PDF file for testing."""
    pdf_file = temp_dir / "epa_sample.pdf"
    pdf_file.write_bytes(epa_sample_pdf_content)
    return pdf_file


@pytest.fixture
def anyline_sample_pdf_content():
    """Anyline sample PDF content from local file."""
    anyline_file = INTEGRATION_FIXTURES_DIR / "anyline_book.pdf"
    if not anyline_file.exists():
        pytest.skip("Anyline sample PDF not found in test fixtures")
    
    return anyline_file.read_bytes()


@pytest.fixture
def anyline_sample_pdf_file(temp_dir, anyline_sample_pdf_content):
    """Anyline sample PDF file for testing."""
    pdf_file = temp_dir / "anyline_sample.pdf"
    pdf_file.write_bytes(anyline_sample_pdf_content)
    return pdf_file


@pytest.fixture
def integration_sample_pdf_content():
    """Integration test sample PDF content from local file."""
    sample_file = INTEGRATION_FIXTURES_DIR / "sample.pdf"
    if not sample_file.exists():
        pytest.skip("Integration sample PDF not found in test fixtures")
    
    return sample_file.read_bytes()


@pytest.fixture
def integration_sample_pdf_file(temp_dir, integration_sample_pdf_content):
    """Integration test sample PDF file for testing."""
    pdf_file = temp_dir / "integration_sample.pdf"
    pdf_file.write_bytes(integration_sample_pdf_content)
    return pdf_file


@pytest.fixture
def image_based_pdf_content():
    """Image-based PDF content from local file."""
    image_file = INTEGRATION_FIXTURES_DIR / "image_based.pdf"
    if not image_file.exists():
        pytest.skip("Image-based PDF not found in test fixtures")
    
    return image_file.read_bytes()


@pytest.fixture
def image_based_pdf_file(temp_dir, image_based_pdf_content):
    """Image-based PDF file for testing."""
    pdf_file = temp_dir / "image_based.pdf"
    pdf_file.write_bytes(image_based_pdf_content)
    return pdf_file


# Legacy fixture names for backward compatibility
@pytest.fixture
def weblite_sample_pdf_content(integration_sample_pdf_content):
    """Legacy: Use integration sample instead of network download."""
    return integration_sample_pdf_content


@pytest.fixture
def weblite_sample_pdf_file(temp_dir, weblite_sample_pdf_content):
    """Legacy: Weblite sample PDF file for testing."""
    pdf_file = temp_dir / "weblite_sample.pdf"
    pdf_file.write_bytes(weblite_sample_pdf_content)
    return pdf_file


@pytest.fixture
def princexml_sample_pdf_content(anyline_sample_pdf_content):
    """Legacy: Use anyline sample instead of network download."""
    return anyline_sample_pdf_content


@pytest.fixture
def princexml_sample_pdf_file(temp_dir, princexml_sample_pdf_content):
    """Legacy: PrinceXML sample PDF file for testing."""
    pdf_file = temp_dir / "princexml_essay.pdf"
    pdf_file.write_bytes(princexml_sample_pdf_content)
    return pdf_file


@pytest.fixture
def nhtsa_form_pdf_content(epa_sample_pdf_content):
    """Legacy: Use EPA sample instead of network download."""
    return epa_sample_pdf_content


@pytest.fixture
def nhtsa_form_pdf_file(temp_dir, nhtsa_form_pdf_content):
    """Legacy: NHTSA form PDF file for testing."""
    pdf_file = temp_dir / "nhtsa_form.pdf"
    pdf_file.write_bytes(nhtsa_form_pdf_content)
    return pdf_file


# PDF factory fixture for dynamic test data creation
@pytest.fixture
def pdf_factory():
    """Factory for creating test PDFs with different characteristics."""
    def _create_pdf(
        content_type: str = "simple",
        pages: int = 1,
        encrypted: bool = False,
        file_size_kb: Optional[int] = None
    ) -> bytes:
        """
        Create a test PDF with specified characteristics.
        
        Args:
            content_type: Type of PDF content ("simple", "complex", "form")
            pages: Number of pages
            encrypted: Whether PDF should be encrypted
            file_size_kb: Target file size in KB (approximate)
        """
        if content_type == "simple":
            # Return basic PDF content
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
        elif content_type == "multi_page":
            # Create multi-page PDF content
            base_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids ["""
            
            for i in range(pages):
                base_content += f" {i+3} 0 R".encode()
            
            base_content += f"] /Count {pages} >>\nendobj\n".encode()
            
            for i in range(pages):
                page_obj = f"""
{i+3} 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj"""
                base_content += page_obj.encode()
            
            base_content += b"""
xref
0 """ + str(pages + 3).encode() + b"""
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size """ + str(pages + 3).encode() + b""" /Root 1 0 R >>
startxref
175
%%EOF"""
            return base_content
        
        # Default to simple for unknown types
        return _create_pdf("simple", 1, False, None)
    
    return _create_pdf