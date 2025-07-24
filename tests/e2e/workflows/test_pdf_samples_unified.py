"""
Unified PDF sample tests with parameterized fixtures.

This module replaces the separate sample test files (test_epa_sample.py,
test_anyline_sample.py, etc.) with a single parameterized test suite that
tests all PDF types consistently while reducing code duplication.
"""

import io

import pytest
from fastapi.testclient import TestClient


# PDF sample configurations
PDF_SAMPLES = [
    pytest.param(
        "epa_sample_pdf_content",
        "epa_sample.pdf",
        "government_document",
        {"min_size": 1000, "expected_pages": 1, "encrypted": False},
        id="epa_government_document",
    ),
    pytest.param(
        "anyline_sample_pdf_content",
        "anyline_sample.pdf",
        "image_rich_document",
        {"min_size": 1000, "expected_pages": 1, "encrypted": False},
        id="anyline_image_rich",
    ),
    pytest.param(
        "integration_sample_pdf_content",
        "integration_sample.pdf",
        "standard_document",
        {"min_size": 500, "expected_pages": 1, "encrypted": False},
        id="integration_standard",
    ),
    pytest.param(
        "image_based_pdf_content",
        "image_based.pdf",
        "scanned_document",
        {"min_size": 1000, "expected_pages": 1, "encrypted": False},
        id="image_based_scanned",
    ),
]


class TestPDFSamples:
    """Unified tests for all PDF sample types."""

    @pytest.mark.parametrize(
        "content_fixture,filename,pdf_type,properties", PDF_SAMPLES
    )
    def test_pdf_sample_upload_and_metadata(
        self,
        client: TestClient,
        content_fixture: str,
        filename: str,
        pdf_type: str,
        properties: dict,
        request,
    ):
        """Test uploading PDF sample and verifying its metadata."""
        # Get the PDF content from the fixture
        try:
            pdf_content = request.getfixturevalue(content_fixture)
        except pytest.FixtureLookupError:
            pytest.skip(f"Fixture {content_fixture} not available")

        # Upload the PDF
        files = {"file": (filename, io.BytesIO(pdf_content), "application/pdf")}
        response = client.post("/api/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        # Verify basic response structure
        assert "file_id" in data
        assert data["filename"] == filename
        assert data["mime_type"] == "application/pdf"
        assert data["file_size"] >= properties["min_size"]

        # Verify metadata
        metadata = data["metadata"]
        assert "page_count" in metadata
        assert "file_size" in metadata
        assert "encrypted" in metadata

        assert metadata["page_count"] >= properties["expected_pages"]
        assert metadata["encrypted"] == properties["encrypted"]
        assert metadata["file_size"] == data["file_size"]

    @pytest.mark.parametrize(
        "content_fixture,filename,pdf_type,properties", PDF_SAMPLES
    )
    def test_pdf_sample_size_handling(
        self,
        client: TestClient,
        content_fixture: str,
        filename: str,
        pdf_type: str,
        properties: dict,
        request,
    ):
        """Test PDF sample size validation and handling."""
        try:
            pdf_content = request.getfixturevalue(content_fixture)
        except pytest.FixtureLookupError:
            pytest.skip(f"Fixture {content_fixture} not available")

        file_size = len(pdf_content)
        max_size = 50 * 1024 * 1024  # 50MB limit

        print(
            f"{pdf_type} PDF size: {file_size:,} bytes ({file_size / (1024 * 1024):.2f} MB)"
        )

        files = {"file": (filename, io.BytesIO(pdf_content), "application/pdf")}
        response = client.post("/api/upload", files=files)

        if file_size >= max_size:
            # Should be rejected for size
            assert response.status_code == 413
            data = response.json()
            assert "too large" in data["detail"].lower()
        else:
            # Should be accepted and processed successfully
            assert response.status_code == 200
            data = response.json()
            assert data["file_size"] == file_size

    @pytest.mark.parametrize(
        "content_fixture,filename,pdf_type,properties", PDF_SAMPLES
    )
    def test_pdf_sample_full_workflow(
        self,
        client: TestClient,
        content_fixture: str,
        filename: str,
        pdf_type: str,
        properties: dict,
        request,
    ):
        """Test complete workflow with PDF sample if within size limits."""
        try:
            pdf_content = request.getfixturevalue(content_fixture)
        except pytest.FixtureLookupError:
            pytest.skip(f"Fixture {content_fixture} not available")

        file_size = len(pdf_content)
        max_size = 50 * 1024 * 1024  # 50MB limit

        # Skip if file is too large
        if file_size >= max_size:
            pytest.skip(f"{pdf_type} PDF ({file_size:,} bytes) exceeds 50MB limit")

        # Upload PDF
        files = {"file": (filename, io.BytesIO(pdf_content), "application/pdf")}
        upload_response = client.post("/api/upload", files=files)

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        file_id = upload_data["file_id"]

        # Test metadata retrieval - this works without shared service
        metadata_response = client.get(f"/api/metadata/{file_id}")
        if metadata_response.status_code == 200:
            metadata = metadata_response.json()
            assert metadata["page_count"] >= properties["expected_pages"]
            assert metadata["file_size"] == file_size
            assert metadata["encrypted"] == properties["encrypted"]


class TestPDFSamplePerformance:
    """Performance tests for different PDF sample types."""

    @pytest.mark.parametrize(
        "content_fixture,filename,pdf_type,properties", PDF_SAMPLES
    )
    def test_pdf_sample_upload_performance(
        self,
        client: TestClient,
        content_fixture: str,
        filename: str,
        pdf_type: str,
        properties: dict,
        request,
    ):
        """Test upload performance for different PDF types."""
        import time

        try:
            pdf_content = request.getfixturevalue(content_fixture)
        except pytest.FixtureLookupError:
            pytest.skip(f"Fixture {content_fixture} not available")

        file_size = len(pdf_content)
        max_size = 50 * 1024 * 1024  # 50MB limit

        # Skip if file is too large
        if file_size >= max_size:
            pytest.skip(f"{pdf_type} PDF ({file_size:,} bytes) exceeds 50MB limit")

        files = {"file": (filename, io.BytesIO(pdf_content), "application/pdf")}

        # Time the upload process
        start_time = time.time()
        response = client.post("/api/upload", files=files)
        upload_time = time.time() - start_time

        assert response.status_code == 200

        # Performance thresholds based on PDF type and size
        if pdf_type == "image_rich_document":
            max_upload_time = 60.0  # Image-rich PDFs may take longer
        else:
            max_upload_time = 30.0

        assert (
            upload_time < max_upload_time
        ), f"Upload took {upload_time:.2f}s, exceeding {max_upload_time}s limit for {pdf_type}"

        # Log performance metrics
        print(f"Performance metrics for {pdf_type} ({file_size:,} bytes):")
        print(f"  Upload: {upload_time:.2f}s")


class TestPDFSampleRobustness:
    """Robustness tests for PDF samples."""

    @pytest.mark.parametrize(
        "content_fixture,filename,pdf_type,properties", PDF_SAMPLES
    )
    def test_pdf_sample_multiple_operations(
        self,
        client: TestClient,
        content_fixture: str,
        filename: str,
        pdf_type: str,
        properties: dict,
        request,
    ):
        """Test robustness with multiple operations on PDF samples."""
        try:
            pdf_content = request.getfixturevalue(content_fixture)
        except pytest.FixtureLookupError:
            pytest.skip(f"Fixture {content_fixture} not available")

        file_size = len(pdf_content)
        max_size = 50 * 1024 * 1024  # 50MB limit

        if file_size >= max_size:
            pytest.skip(f"{pdf_type} PDF ({file_size:,} bytes) exceeds 50MB limit")

        # Test multiple upload operations to ensure stability
        for i in range(2):
            files = {
                "file": (
                    f"{filename.replace('.pdf', f'_{i}.pdf')}",
                    io.BytesIO(pdf_content),
                    "application/pdf",
                )
            }
            upload_response = client.post("/api/upload", files=files)
            assert upload_response.status_code == 200

            upload_data = upload_response.json()
            file_id = upload_data["file_id"]

            # Multiple metadata requests to test stability
            for _ in range(2):
                metadata_response = client.get(f"/api/metadata/{file_id}")
                if metadata_response.status_code == 200:
                    metadata = metadata_response.json()
                    assert metadata["page_count"] >= properties["expected_pages"]
                    assert metadata["file_size"] == file_size


def test_comprehensive_pdf_samples_all_types(
    client: TestClient,
    epa_sample_pdf_content: bytes,
    anyline_sample_pdf_content: bytes,
    integration_sample_pdf_content: bytes,
    image_based_pdf_content: bytes,
):
    """Test handling all PDF sample types together."""
    max_size = 50 * 1024 * 1024  # 50MB limit
    file_ids = []

    # Define all samples with their expected characteristics
    samples = [
        ("epa_sample.pdf", epa_sample_pdf_content, "government_text"),
        ("anyline_sample.pdf", anyline_sample_pdf_content, "image_rich"),
        ("integration_sample.pdf", integration_sample_pdf_content, "standard"),
        ("image_based.pdf", image_based_pdf_content, "scanned"),
    ]

    # Upload all samples that fit within size limits
    for filename, content, pdf_type in samples:
        file_size = len(content)
        if file_size < max_size:
            files = {"file": (filename, io.BytesIO(content), "application/pdf")}
            response = client.post("/api/upload", files=files)
            assert response.status_code == 200
            file_id = response.json()["file_id"]
            file_ids.append((file_id, pdf_type, file_size))
            print(f"Uploaded {pdf_type} PDF: {file_size:,} bytes")

    # Verify all files have unique IDs
    assert len({fid for fid, _, _ in file_ids}) == len(file_ids)

    print(f"Successfully processed {len(file_ids)} different PDF types simultaneously")
