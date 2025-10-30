import pytest
from fastapi.testclient import TestClient

from conftest import (
    assert_error_response,
    assert_metadata_fields,
    assert_upload_response,
    create_upload_files,
    perform_full_pdf_workflow,
)


def test_nhtsa_form_upload_and_metadata(
    client: TestClient, nhtsa_form_pdf_content: bytes
):
    """Test uploading the NHTSA PDF form and verifying its metadata."""
    files = create_upload_files("nhtsa_form.pdf", nhtsa_form_pdf_content)
    response = client.post("/api/upload", files=files)

    assert_upload_response(response, expected_filename="nhtsa_form.pdf")
    data = response.json()

    # Check metadata for NHTSA form PDF
    metadata = data["metadata"]
    assert_metadata_fields(metadata)
    assert not metadata["encrypted"]  # Government forms typically not encrypted


def test_nhtsa_form_size_and_handling(
    client: TestClient, nhtsa_form_pdf_content: bytes
):
    """Test that NHTSA PDF form is handled correctly within size limits."""
    file_size = len(nhtsa_form_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit

    # Log the actual file size for debugging
    print(
        f"NHTSA form PDF size: {file_size:,} bytes ({file_size / (1024 * 1024):.2f} MB)"
    )

    # Test upload
    files = create_upload_files("nhtsa_form.pdf", nhtsa_form_pdf_content)
    response = client.post("/api/upload", files=files)

    if file_size >= max_size:
        # Should be rejected for size
        assert_error_response(response, 413, "too large")
    else:
        # Should be accepted and processed successfully
        assert_upload_response(response, expected_filename="nhtsa_form.pdf")
        data = response.json()
        assert data["file_size"] == file_size

        # Verify metadata extraction works with form PDFs
        metadata = data["metadata"]
        assert_metadata_fields(metadata)
        assert not metadata["encrypted"]


def test_nhtsa_form_full_workflow(client: TestClient, nhtsa_form_pdf_content: bytes):
    """Test the complete workflow with NHTSA PDF form if within size limits."""
    file_size = len(nhtsa_form_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit

    # Skip if file is too large for our current limits
    if file_size >= max_size:
        pytest.skip(
            f"NHTSA form PDF ({file_size:,} bytes) exceeds 50MB limit - testing size rejection instead"
        )

    perform_full_pdf_workflow(client, "nhtsa_form.pdf", nhtsa_form_pdf_content)


def test_nhtsa_form_structured_content_performance(
    client: TestClient, nhtsa_form_pdf_content: bytes
):
    """Test performance characteristics with structured PDF form content."""
    import time

    file_size = len(nhtsa_form_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit

    # Skip if file is too large
    if file_size >= max_size:
        pytest.skip(f"NHTSA form PDF ({file_size:,} bytes) exceeds 50MB limit")

    import time

    files = create_upload_files("nhtsa_form.pdf", nhtsa_form_pdf_content)

    # Time the upload process for form content
    start_time = time.time()
    response = client.post("/api/upload", files=files)
    upload_time = time.time() - start_time

    assert response.status_code == 200
    data = response.json()
    file_id = data["file_id"]

    # Upload should complete in reasonable time
    assert (
        upload_time < 30.0
    ), f"Upload took {upload_time:.2f} seconds, which may be too slow"

    # Time the metadata retrieval
    start_time = time.time()
    metadata_response = client.get(f"/api/metadata/{file_id}")
    metadata_time = time.time() - start_time

    assert metadata_response.status_code == 200
    assert metadata_time < 5.0, f"Metadata extraction took {metadata_time:.2f} seconds"

    # Time the file retrieval
    start_time = time.time()
    pdf_response = client.get(f"/api/pdf/{file_id}")
    retrieval_time = time.time() - start_time

    assert pdf_response.status_code == 200
    assert retrieval_time < 10.0, f"File retrieval took {retrieval_time:.2f} seconds"

    # Clean up
    client.delete(f"/api/pdf/{file_id}")

    # Log performance metrics for form content
    print(f"Performance metrics for {file_size:,} byte PDF form:")
    print(f"  Upload: {upload_time:.2f}s")
    print(f"  Metadata: {metadata_time:.2f}s")
    print(f"  Retrieval: {retrieval_time:.2f}s")


def test_comprehensive_pdf_samples_all_types(
    client: TestClient,
    epa_sample_pdf_content: bytes,
    weblite_sample_pdf_content: bytes,
    princexml_sample_pdf_content: bytes,
    anyline_sample_pdf_content: bytes,
    nhtsa_form_pdf_content: bytes,
):
    """Test handling all PDF sample types including government forms."""
    max_size = 50 * 1024 * 1024  # 50MB limit

    file_ids = []

    # Define all samples with their expected characteristics
    samples = [
        ("epa_sample.pdf", epa_sample_pdf_content, "government_text"),
        ("weblite_sample.pdf", weblite_sample_pdf_content, "scanned_ocr"),
        ("princexml_essay.pdf", princexml_sample_pdf_content, "structured_text"),
        ("anyline_sample.pdf", anyline_sample_pdf_content, "image_rich"),
        ("nhtsa_form.pdf", nhtsa_form_pdf_content, "form_fields"),
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

    # Verify all can be retrieved and have valid metadata
    for file_id, _pdf_type, file_size in file_ids:
        # Test retrieval
        pdf_response = client.get(f"/api/pdf/{file_id}")
        assert pdf_response.status_code == 200
        assert len(pdf_response.content) == file_size

        # Test metadata
        metadata_response = client.get(f"/api/metadata/{file_id}")
        assert metadata_response.status_code == 200
        metadata = metadata_response.json()
        assert metadata["page_count"] > 0
        assert metadata["file_size"] == file_size
        assert not metadata["encrypted"]

    print(f"Successfully processed {len(file_ids)} different PDF types simultaneously")

    # Clean up all uploaded files
    for file_id, _, _ in file_ids:
        delete_response = client.delete(f"/api/pdf/{file_id}")
        assert delete_response.status_code == 200


def test_nhtsa_form_government_pdf_robustness(
    client: TestClient, nhtsa_form_pdf_content: bytes
):
    """Test robustness when processing government PDF forms with potential complex structures."""
    file_size = len(nhtsa_form_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit

    if file_size >= max_size:
        pytest.skip(f"NHTSA form PDF ({file_size:,} bytes) exceeds 50MB limit")

    # Test multiple operations to ensure stability with government forms
    for i in range(2):  # Upload, process, delete cycle 2 times
        files = {
            "file": (
                f"nhtsa_form_{i}.pdf",
                io.BytesIO(nhtsa_form_pdf_content),
                "application/pdf",
            )
        }

        # Upload
        upload_response = client.post("/api/upload", files=files)
        assert upload_response.status_code == 200
        file_id = upload_response.json()["file_id"]

        # Multiple metadata requests to test stability
        for _ in range(3):
            metadata_response = client.get(f"/api/metadata/{file_id}")
            assert metadata_response.status_code == 200
            metadata = metadata_response.json()
            assert metadata["page_count"] > 0
            # Government forms should maintain consistent metadata
            assert metadata["file_size"] == file_size

        # Multiple retrieval requests
        for _ in range(2):
            pdf_response = client.get(f"/api/pdf/{file_id}")
            assert pdf_response.status_code == 200
            assert len(pdf_response.content) == file_size

        # Clean up
        delete_response = client.delete(f"/api/pdf/{file_id}")
        assert delete_response.status_code == 200
