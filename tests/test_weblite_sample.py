from fastapi.testclient import TestClient

from conftest import (
    assert_metadata_fields,
    assert_upload_response,
    create_upload_files,
    perform_full_pdf_workflow,
)


def test_weblite_sample_upload_and_metadata(
    client: TestClient, weblite_sample_pdf_content: bytes
):
    """Test uploading the Weblite OCR sample PDF and verifying its metadata."""
    files = create_upload_files("weblite_sample.pdf", weblite_sample_pdf_content)
    response = client.post("/api/upload", files=files)

    assert_upload_response(response, expected_filename="weblite_sample.pdf")
    data = response.json()

    # Check metadata for Weblite PDF
    metadata = data["metadata"]
    assert_metadata_fields(metadata)
    assert not metadata["encrypted"]  # Weblite sample should not be encrypted


def test_weblite_sample_full_workflow(
    client: TestClient, weblite_sample_pdf_content: bytes
):
    """Test the complete workflow with Weblite OCR sample PDF."""
    perform_full_pdf_workflow(client, "weblite_sample.pdf", weblite_sample_pdf_content)


def test_weblite_sample_scanned_pdf_handling(
    client: TestClient, weblite_sample_pdf_content: bytes
):
    """Test that Weblite scanned PDF sample is handled correctly."""
    # This PDF is specifically a scanned document sample, good for OCR testing
    files = create_upload_files("weblite_sample.pdf", weblite_sample_pdf_content)
    response = client.post("/api/upload", files=files)

    assert_upload_response(response, expected_filename="weblite_sample.pdf")
    data = response.json()

    # Check that metadata extraction works for scanned PDFs
    assert_metadata_fields(data["metadata"])


def test_multiple_pdf_samples_comparison(
    client: TestClient, epa_sample_pdf_content: bytes, weblite_sample_pdf_content: bytes
):
    """Test handling multiple different PDF samples to ensure system robustness."""
    # Upload EPA sample
    epa_files = create_upload_files("epa_sample.pdf", epa_sample_pdf_content)
    epa_response = client.post("/api/upload", files=epa_files)
    assert epa_response.status_code == 200
    epa_data = epa_response.json()
    epa_file_id = epa_data["file_id"]

    # Upload Weblite sample
    weblite_files = create_upload_files("weblite_sample.pdf", weblite_sample_pdf_content)
    weblite_response = client.post("/api/upload", files=weblite_files)
    assert weblite_response.status_code == 200
    weblite_data = weblite_response.json()
    weblite_file_id = weblite_data["file_id"]

    # Verify both files have different IDs
    assert epa_file_id != weblite_file_id

    # Verify both files can be retrieved independently
    epa_pdf_response = client.get(f"/api/pdf/{epa_file_id}")
    weblite_pdf_response = client.get(f"/api/pdf/{weblite_file_id}")

    assert epa_pdf_response.status_code == 200
    assert weblite_pdf_response.status_code == 200

    # Verify metadata for both
    epa_metadata_response = client.get(f"/api/metadata/{epa_file_id}")
    weblite_metadata_response = client.get(f"/api/metadata/{weblite_file_id}")

    assert epa_metadata_response.status_code == 200
    assert weblite_metadata_response.status_code == 200

    epa_metadata = epa_metadata_response.json()
    weblite_metadata = weblite_metadata_response.json()

    # Both should have valid metadata but potentially different characteristics
    assert_metadata_fields(epa_metadata)
    assert_metadata_fields(weblite_metadata)
    assert not epa_metadata["encrypted"]
    assert not weblite_metadata["encrypted"]

    # Clean up both files
    epa_delete_response = client.delete(f"/api/pdf/{epa_file_id}")
    weblite_delete_response = client.delete(f"/api/pdf/{weblite_file_id}")

    assert epa_delete_response.status_code == 200
    assert weblite_delete_response.status_code == 200
