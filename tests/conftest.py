"""
Test configuration and fixtures.

This module provides all shared fixtures for the test suite, eliminating
network dependencies and improving test reliability and performance.
Now enhanced with fixture factories for better maintainability.
"""

import tempfile
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from tests.config import TestConstants
from tests.helpers.mock_optimization import OptimizedPDFMocks, MockResponseFactory

# Test data directory (legacy compatibility)
TEST_FIXTURES_DIR = TestConstants.FIXTURES_DIR
INTEGRATION_FIXTURES_DIR = TestConstants.INTEGRATION_FIXTURES_DIR


@pytest.fixture(scope="session")
def client():
    """Test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture(scope="session")
def temp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(scope="session")
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
@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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


# ==================== FIXTURE FACTORIES ====================
# Enhanced fixture factories for improved test maintainability


@pytest.fixture(scope="session")
def pdf_sample_factory():
    """Factory for loading real PDF samples by name with fallback logic."""

    def _load_sample(sample_name: str) -> bytes:
        """Load a PDF sample by name."""
        config = TestConstants.REAL_PDF_SAMPLES.get(sample_name)
        if not config:
            pytest.skip(f"PDF sample '{sample_name}' not configured")

        # Try primary filename first
        filename = config["filename"]
        file_path = TestConstants.FIXTURES_DIR / filename

        if not file_path.exists():
            # Try integration fixtures directory
            file_path = TestConstants.INTEGRATION_FIXTURES_DIR / filename

        if not file_path.exists() and config.get("fallback_filename"):
            # Try fallback filename
            fallback_filename = config["fallback_filename"]
            file_path = TestConstants.INTEGRATION_FIXTURES_DIR / fallback_filename

        if not file_path.exists():
            pytest.skip(f"PDF sample file not found: {filename}")

        return file_path.read_bytes()

    return _load_sample


@pytest.fixture(scope="session")
def mock_response_factory():
    """Factory for creating mock API responses with different characteristics."""

    def _create_response(
        response_type: str = "upload_success", **overrides: Any
    ) -> Dict[str, Any]:
        """Create a mock response based on type and overrides."""
        base_template = TestConstants.MOCK_RESPONSE_TEMPLATES.get(response_type, {})

        if response_type == "upload_success":
            return {
                "file_id": overrides.get("file_id", str(uuid.uuid4())),
                "filename": overrides.get("filename", "test.pdf"),
                "mime_type": overrides.get("mime_type", "application/pdf"),
                "file_size": overrides.get("file_size", TestConstants.MEDIUM_FILE_SIZE),
                "upload_timestamp": overrides.get(
                    "upload_timestamp", "2024-01-01T12:00:00Z"
                ),
                "metadata": {
                    "page_count": overrides.get("page_count", 1),
                    "file_size": overrides.get(
                        "file_size", TestConstants.MEDIUM_FILE_SIZE
                    ),
                    "encrypted": overrides.get("encrypted", False),
                    **overrides.get("metadata", {}),
                },
                **{
                    k: v
                    for k, v in overrides.items()
                    if k not in ["metadata", "page_count", "file_size", "encrypted"]
                },
            }
        elif response_type == "metadata_success":
            return {
                "page_count": overrides.get("page_count", 1),
                "file_size": overrides.get("file_size", TestConstants.MEDIUM_FILE_SIZE),
                "encrypted": overrides.get("encrypted", False),
                "creation_date": overrides.get("creation_date", "2024-01-01T12:00:00Z"),
                "modification_date": overrides.get(
                    "modification_date", "2024-01-01T12:00:00Z"
                ),
                **overrides,
            }
        else:
            # Use template and apply overrides
            result = dict(base_template)
            result.update(overrides)
            return result

    return _create_response


@pytest.fixture(scope="session")
def test_client_factory():
    """Factory for creating test clients with different configurations."""

    def _create_client(
        client_type: str = "sync",
        base_url: str = TestConstants.DEFAULT_BASE_URL,
        headers: Optional[Dict[str, str]] = None,
    ) -> TestClient:
        """Create a test client with specified configuration."""
        client_kwargs = {"base_url": base_url}

        if headers:
            client_kwargs["headers"] = headers

        if client_type == "sync":
            return TestClient(app, **client_kwargs)
        else:
            raise ValueError(f"Unsupported client type: {client_type}")

    return _create_client


@pytest.fixture(scope="session")
def pdf_characteristics_factory():
    """Factory for creating PDF content with specific characteristics."""

    def _create_pdf_with_characteristics(
        document_type: str = "simple",
        pages: int = 1,
        file_size_target_kb: Optional[int] = None,
        has_text: bool = True,
        has_images: bool = False,
        encrypted: bool = False,
        **kwargs: Any,
    ) -> bytes:
        """Create PDF content with specified characteristics."""
        if document_type in TestConstants.PDF_SAMPLES:
            config = TestConstants.PDF_SAMPLES[document_type]
            # Use config defaults, override with parameters
            pages = kwargs.get("pages", config.get("expected_pages", pages))
            has_text = kwargs.get("has_text", config.get("has_text", has_text))
            has_images = kwargs.get("has_images", config.get("has_images", has_images))
            encrypted = kwargs.get("encrypted", config.get("encrypted", encrypted))

        # Generate PDF content based on document type
        if document_type == "simple":
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
        elif document_type == "multi_page":
            # Create multi-page PDF content
            base_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids ["""

            for i in range(pages):
                base_content += f" {i + 3} 0 R".encode()

            base_content += f"] /Count {pages} >>\nendobj\n".encode()

            for i in range(pages):
                page_obj = f"""
{i + 3} 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj"""
                base_content += page_obj.encode()

            base_content += (
                b"""
xref
0 """
                + str(pages + 3).encode()
                + b"""
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size """
                + str(pages + 3).encode()
                + b""" /Root 1 0 R >>
startxref
175
%%EOF"""
            )
            return base_content
        else:
            # Default to simple PDF
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

    return _create_pdf_with_characteristics


# Legacy compatibility fixtures removed - use pdf_sample_factory directly
# Example: pdf_sample_factory("epa_sample") instead of epa_sample_pdf_content


# PDF factory fixture for dynamic test data creation (enhanced)
@pytest.fixture(scope="session")
def pdf_factory():
    """Factory for creating test PDFs with different characteristics."""

    def _create_pdf(
        content_type: str = "simple",
        pages: int = 1,
        encrypted: bool = False,
        file_size_kb: Optional[int] = None,
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
                base_content += f" {i + 3} 0 R".encode()

            base_content += f"] /Count {pages} >>\nendobj\n".encode()

            for i in range(pages):
                page_obj = f"""
{i + 3} 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj"""
                base_content += page_obj.encode()

            base_content += (
                b"""
xref
0 """
                + str(pages + 3).encode()
                + b"""
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size """
                + str(pages + 3).encode()
                + b""" /Root 1 0 R >>
startxref
175
%%EOF"""
            )
            return base_content

        # Default to simple for unknown types
        return _create_pdf("simple", 1, False, None)

    return _create_pdf


# ==================== PERFORMANCE OPTIMIZATION FIXTURES ====================


@pytest.fixture(scope="session")
def optimized_mocks():
    """Session-scoped optimized mocks for performance testing."""
    return OptimizedPDFMocks()


@pytest.fixture(scope="session")
def fast_mock_responses():
    """Session-scoped fast mock response factory."""
    return MockResponseFactory()


@pytest.fixture(scope="session", autouse=True)
def optimize_test_environment(request):
    """Auto-use fixture to optimize test environment based on test type."""
    if "unit" in request.node.keywords:
        # Apply unit test optimizations
        with patch("backend.app.services.pdf_service.PDFService") as mock_service:
            mock_service.return_value = OptimizedPDFMocks.mock_pdf_service()
            yield
    else:
        # No optimizations for integration tests
        yield


@pytest.fixture
def mock_pdf_service():
    """Mock PDF service for unit tests."""
    return OptimizedPDFMocks.mock_pdf_service()


@pytest.fixture
def mock_async_pdf_service():
    """Mock async PDF service for unit tests."""
    return OptimizedPDFMocks.mock_async_pdf_service()


@pytest.fixture(scope="session")
def performance_benchmark():
    """Fixture to track and report performance metrics."""
    metrics = {}

    def record_metric(test_name: str, metric_name: str, value: float):
        """Record a performance metric."""
        if test_name not in metrics:
            metrics[test_name] = {}
        metrics[test_name][metric_name] = value

    def get_metrics(test_name: str = None):
        """Get recorded metrics."""
        if test_name:
            return metrics.get(test_name, {})
        return metrics

    def report_metrics():
        """Print performance report."""
        if metrics:
            print("\n=== Performance Metrics ===")
            for test_name, test_metrics in metrics.items():
                print(f"{test_name}:")
                for metric_name, value in test_metrics.items():
                    print(f"  {metric_name}: {value:.3f}")

    benchmark = type(
        "Benchmark",
        (),
        {
            "record": record_metric,
            "get": get_metrics,
            "report": report_metrics,
            "metrics": metrics,
        },
    )()

    yield benchmark

    # Report metrics at session end
    benchmark.report_metrics()
