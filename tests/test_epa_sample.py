from fastapi.testclient import TestClient

from conftest import (
    assert_metadata_fields,
    assert_upload_response,
    create_upload_files,
    perform_full_pdf_workflow,
)


def test_epa_sample_upload_and_metadata(
    client: TestClient, epa_sample_pdf_content: bytes
):
    """Test uploading the EPA sample PDF and verifying its metadata."""
    files = create_upload_files("epa_sample.pdf", epa_sample_pdf_content)
    response = client.post("/api/upload", files=files)

    assert_upload_response(response, expected_filename="epa_sample.pdf")
    data = response.json()

    # Check metadata for EPA PDF
    metadata = data["metadata"]
    assert_metadata_fields(metadata)
    assert not metadata["encrypted"]  # EPA sample should not be encrypted


def test_epa_sample_full_workflow(client: TestClient, epa_sample_pdf_content: bytes):
    """Test the complete workflow with EPA sample PDF."""
    perform_full_pdf_workflow(client, "epa_sample.pdf", epa_sample_pdf_content)


def test_epa_sample_large_file_handling(
    client: TestClient, epa_sample_pdf_content: bytes
):
    """Test that EPA sample PDF is handled correctly even if it's larger."""
    # Verify the EPA sample is within our size limits
    file_size = len(epa_sample_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit

    assert (
        file_size < max_size
    ), f"EPA sample PDF ({file_size} bytes) exceeds size limit ({max_size} bytes)"

    # Upload and verify
    files = {
        "file": (
            "epa_sample.pdf",
            io.BytesIO(epa_sample_pdf_content),
            "application/pdf",
        )
    }
    response = client.post("/api/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["file_size"] == file_size
