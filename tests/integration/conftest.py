"""
Shared fixtures and configuration for integration tests.
"""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from backend.app.main import app

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    """Create a test client for synchronous tests."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for async tests."""
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
def sample_pdf_path() -> Path:
    """Get path to sample PDF file."""
    # Use EPA sample as the default test PDF
    return TEST_DATA_DIR / "epa_sample.pdf"


@pytest.fixture(scope="session")
def large_pdf_path() -> Path:
    """Get path to large PDF file for performance testing."""
    return TEST_DATA_DIR / "large_sample.pdf"


@pytest.fixture(scope="session")
def corrupt_pdf_path() -> Path:
    """Get path to corrupt PDF file for error testing."""
    return TEST_DATA_DIR / "corrupt.pdf"


@pytest.fixture(scope="session")
def test_upload_dir(tmp_path_factory) -> Path:
    """Create a session-scoped temporary upload directory for tests."""
    # Create session-scoped temp directory
    session_tmp = tmp_path_factory.mktemp("uploads")
    upload_dir = session_tmp / "test_uploads"
    upload_dir.mkdir(exist_ok=True)

    # Set environment variable for upload directory
    original_upload_dir = os.environ.get("UPLOAD_DIR")
    os.environ["UPLOAD_DIR"] = str(upload_dir)

    yield upload_dir

    # Restore original upload directory
    if original_upload_dir:
        os.environ["UPLOAD_DIR"] = original_upload_dir
    else:
        os.environ.pop("UPLOAD_DIR", None)


@pytest.fixture
def isolated_upload_dir(test_upload_dir, request) -> Path:
    """Create test-specific subdirectory for file isolation."""
    # Create unique subdirectory for this test
    test_name = request.node.name.replace("[", "_").replace("]", "_")
    test_dir = test_upload_dir / test_name
    test_dir.mkdir(exist_ok=True)

    # Temporarily update upload dir for this test
    os.environ["UPLOAD_DIR"] = str(test_dir)

    yield test_dir

    # Restore session upload dir
    os.environ["UPLOAD_DIR"] = str(test_upload_dir)

    # Clean up test-specific files
    import shutil

    if test_dir.exists():
        try:
            shutil.rmtree(test_dir)
        except (OSError, PermissionError):
            # If cleanup fails, just log and continue
            print(f"Warning: Could not clean up {test_dir}")


@pytest.fixture(scope="session")
def mock_pdf_response():
    """Mock PDF analysis response."""
    return {
        "document_id": "123e4567-e89b-12d3-a456-426614174000",
        "filename": "test.pdf",
        "total_pages": 5,
        "has_extractable_text": True,
        "file_size_mb": 1.5,
        "extracted_fields": {
            "personal_info": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "(555) 123-4567",
            },
            "document_info": {
                "type": "Contract",
                "date": "2024-01-15",
                "reference": "REF-12345",
            },
        },
        "confidence_scores": {"personal_info": 0.95, "document_info": 0.87},
        "processing_time_ms": 1250,
    }


@pytest.fixture(scope="session")
def mock_error_response():
    """Mock error response."""
    return {
        "detail": "Failed to process PDF",
        "error_code": "PDF_PROCESSING_ERROR",
        "correlation_id": "test-correlation-id",
    }
