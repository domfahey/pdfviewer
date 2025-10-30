import io
import time

import pytest
from fastapi.testclient import TestClient

from conftest import (
    assert_error_response,
    assert_metadata_fields,
    assert_upload_response,
    create_upload_files,
    perform_full_pdf_workflow,
)


def test_anyline_sample_upload_and_metadata(
    client: TestClient, anyline_sample_pdf_content: bytes
):
    """Test uploading the Anyline sample scan book PDF with complex images and barcodes."""
    files = create_upload_files("anyline_sample.pdf", anyline_sample_pdf_content)
    response = client.post("/api/upload", files=files)

    assert_upload_response(response, expected_filename="anyline_sample.pdf")
    data = response.json()

    # Check metadata for Anyline PDF
    metadata = data["metadata"]
    assert_metadata_fields(metadata)
    assert not metadata["encrypted"]  # Should not be encrypted


def test_anyline_sample_complex_content_handling(
    client: TestClient, anyline_sample_pdf_content: bytes
):
    """Test that Anyline PDF with complex images and barcodes is handled correctly."""
    file_size = len(anyline_sample_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit

    # Log the actual file size for debugging
    print(f"Anyline PDF size: {file_size:,} bytes ({file_size / (1024 * 1024):.2f} MB)")

    # Test upload regardless of size to verify handling
    files = create_upload_files("anyline_sample.pdf", anyline_sample_pdf_content)
    response = client.post("/api/upload", files=files)

    if file_size >= max_size:
        # Should be rejected for size
        assert_error_response(response, 413, "too large")
    else:
        # Should be accepted and processed successfully
        assert_upload_response(response, expected_filename="anyline_sample.pdf")
        data = response.json()
        assert data["file_size"] == file_size

        # Verify metadata extraction works with complex image content
        metadata = data["metadata"]
        assert_metadata_fields(metadata)
        assert not metadata["encrypted"]


def test_anyline_sample_full_workflow(
    client: TestClient, anyline_sample_pdf_content: bytes
):
    """Test the complete workflow with Anyline complex image PDF if within size limits."""
    file_size = len(anyline_sample_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit

    # Skip if file is too large for our current limits
    if file_size >= max_size:
        pytest.skip(
            f"Anyline PDF ({file_size:,} bytes) exceeds 50MB limit - testing size rejection instead"
        )

    perform_full_pdf_workflow(client, "anyline_sample.pdf", anyline_sample_pdf_content)


def test_anyline_sample_image_rich_performance(
    client: TestClient, anyline_sample_pdf_content: bytes
):
    """Test performance characteristics with image-rich PDF containing barcodes."""
    file_size = len(anyline_sample_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit

    # Skip if file is too large
    if file_size >= max_size:
        pytest.skip(f"Anyline PDF ({file_size:,} bytes) exceeds 50MB limit")

    files = create_upload_files("anyline_sample.pdf", anyline_sample_pdf_content)

    # Time the upload process for image-heavy content
    start_time = time.time()
    response = client.post("/api/upload", files=files)
    upload_time = time.time() - start_time

    assert response.status_code == 200
    data = response.json()
    file_id = data["file_id"]

    # Upload might take longer for image-heavy PDFs (adjust threshold)
    assert (
        upload_time < 60.0
    ), f"Upload took {upload_time:.2f} seconds, which may be too slow for image-rich content"

    # Time the metadata retrieval (might be slower for complex PDFs)
    start_time = time.time()
    metadata_response = client.get(f"/api/metadata/{file_id}")
    metadata_time = time.time() - start_time

    assert metadata_response.status_code == 200
    assert metadata_time < 10.0, f"Metadata extraction took {metadata_time:.2f} seconds"

    # Time the file retrieval
    start_time = time.time()
    pdf_response = client.get(f"/api/pdf/{file_id}")
    retrieval_time = time.time() - start_time

    assert pdf_response.status_code == 200
    assert retrieval_time < 15.0, f"File retrieval took {retrieval_time:.2f} seconds"

    # Clean up
    client.delete(f"/api/pdf/{file_id}")

    # Log performance metrics for image-rich content
    print(f"Performance metrics for {file_size:,} byte image-rich PDF:")
    print(f"  Upload: {upload_time:.2f}s")
    print(f"  Metadata: {metadata_time:.2f}s")
    print(f"  Retrieval: {retrieval_time:.2f}s")


def test_comprehensive_pdf_samples_with_complex_content(
    client: TestClient,
    epa_sample_pdf_content: bytes,
    weblite_sample_pdf_content: bytes,
    princexml_sample_pdf_content: bytes,
    anyline_sample_pdf_content: bytes,
):
    """Test handling all PDF sample types including complex image content."""
    anyline_size = len(anyline_sample_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit

    file_ids = []

    # Upload all samples that fit within size limits
    samples = [
        ("epa_sample.pdf", epa_sample_pdf_content),
        ("weblite_sample.pdf", weblite_sample_pdf_content),
        ("princexml_essay.pdf", princexml_sample_pdf_content),
    ]

    # Add Anyline if it fits
    if anyline_size < max_size:
        samples.append(("anyline_sample.pdf", anyline_sample_pdf_content))

    # Upload all samples
    for filename, content in samples:
        files = {"file": (filename, io.BytesIO(content), "application/pdf")}
        response = client.post("/api/upload", files=files)
        assert response.status_code == 200
        file_ids.append(response.json()["file_id"])

    # Verify all files have unique IDs
    assert len(set(file_ids)) == len(file_ids)

    # Verify all can be retrieved
    for file_id in file_ids:
        pdf_response = client.get(f"/api/pdf/{file_id}")
        assert pdf_response.status_code == 200

        metadata_response = client.get(f"/api/metadata/{file_id}")
        assert metadata_response.status_code == 200
        metadata = metadata_response.json()
        assert metadata["page_count"] > 0

    # Test that Anyline PDF is rejected if too large
    if anyline_size >= max_size:
        files = {
            "file": (
                "anyline_sample.pdf",
                io.BytesIO(anyline_sample_pdf_content),
                "application/pdf",
            )
        }
        response = client.post("/api/upload", files=files)
        assert response.status_code == 413

    # Clean up all uploaded files
    for file_id in file_ids:
        delete_response = client.delete(f"/api/pdf/{file_id}")
        assert delete_response.status_code == 200


def test_anyline_sample_barcode_content_robustness(
    client: TestClient, anyline_sample_pdf_content: bytes
):
    """Test robustness when processing PDF with barcodes and complex visual content."""
    file_size = len(anyline_sample_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit

    if file_size >= max_size:
        pytest.skip(f"Anyline PDF ({file_size:,} bytes) exceeds 50MB limit")

    # Test multiple operations to ensure stability with complex content
    for i in range(3):  # Upload, process, delete cycle 3 times
        files = {
            "file": (
                f"anyline_sample_{i}.pdf",
                io.BytesIO(anyline_sample_pdf_content),
                "application/pdf",
            )
        }

        # Upload
        upload_response = client.post("/api/upload", files=files)
        assert upload_response.status_code == 200
        file_id = upload_response.json()["file_id"]

        # Multiple metadata requests to test stability
        for _ in range(2):
            metadata_response = client.get(f"/api/metadata/{file_id}")
            assert metadata_response.status_code == 200
            metadata = metadata_response.json()
            assert metadata["page_count"] > 0

        # Multiple retrieval requests
        for _ in range(2):
            pdf_response = client.get(f"/api/pdf/{file_id}")
            assert pdf_response.status_code == 200
            assert len(pdf_response.content) == file_size

        # Clean up
        delete_response = client.delete(f"/api/pdf/{file_id}")
        assert delete_response.status_code == 200
