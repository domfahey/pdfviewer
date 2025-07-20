import io

import pytest
from fastapi.testclient import TestClient


def test_get_pdf_file_not_found(client: TestClient):
    """Test getting a PDF file that doesn't exist."""
    response = client.get("/api/pdf/nonexistent-id")
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_get_metadata_not_found(client: TestClient):
    """Test getting metadata for a file that doesn't exist."""
    response = client.get("/api/metadata/nonexistent-id")
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_delete_pdf_not_found(client: TestClient):
    """Test deleting a PDF file that doesn't exist."""
    response = client.delete("/api/pdf/nonexistent-id")
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_full_pdf_workflow(client: TestClient, sample_pdf_content: bytes):
    """Test the complete PDF workflow: upload, retrieve, get metadata, delete."""
    # Step 1: Upload PDF
    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    upload_response = client.post("/api/upload", files=files)
    
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    file_id = upload_data["file_id"]
    
    # Step 2: Get PDF file
    pdf_response = client.get(f"/api/pdf/{file_id}")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert len(pdf_response.content) > 0
    
    # Step 3: Get metadata
    metadata_response = client.get(f"/api/metadata/{file_id}")
    assert metadata_response.status_code == 200
    metadata = metadata_response.json()
    
    assert "page_count" in metadata
    assert "file_size" in metadata
    assert "encrypted" in metadata
    assert metadata["page_count"] > 0
    
    # Step 4: Delete PDF
    delete_response = client.delete(f"/api/pdf/{file_id}")
    assert delete_response.status_code == 200
    delete_data = delete_response.json()
    assert "deleted successfully" in delete_data["message"]
    
    # Step 5: Verify file is deleted
    pdf_response_after_delete = client.get(f"/api/pdf/{file_id}")
    assert pdf_response_after_delete.status_code == 404