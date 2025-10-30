from fastapi.testclient import TestClient

from conftest import assert_error_response, perform_full_pdf_workflow


def test_get_pdf_file_not_found(client: TestClient):
    """Test getting a PDF file that doesn't exist."""
    response = client.get("/api/pdf/nonexistent-id")
    assert_error_response(response, 404, "not found")


def test_get_metadata_not_found(client: TestClient):
    """Test getting metadata for a file that doesn't exist."""
    response = client.get("/api/metadata/nonexistent-id")
    assert_error_response(response, 404, "not found")


def test_delete_pdf_not_found(client: TestClient):
    """Test deleting a PDF file that doesn't exist."""
    response = client.delete("/api/pdf/nonexistent-id")
    assert_error_response(response, 404, "not found")


def test_full_pdf_workflow(client: TestClient, sample_pdf_content: bytes):
    """Test the complete PDF workflow: upload, retrieve, get metadata, delete."""
    perform_full_pdf_workflow(client, "test.pdf", sample_pdf_content)
