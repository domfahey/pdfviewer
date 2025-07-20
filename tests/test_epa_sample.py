import io

import pytest
from fastapi.testclient import TestClient


def test_epa_sample_upload_and_metadata(client: TestClient, epa_sample_pdf_content: bytes):
    """Test uploading the EPA sample PDF and verifying its metadata."""
    files = {"file": ("epa_sample.pdf", io.BytesIO(epa_sample_pdf_content), "application/pdf")}
    
    response = client.post("/api/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "file_id" in data
    assert data["filename"] == "epa_sample.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["file_size"] > 1000  # EPA PDF should be reasonably sized
    
    # Check metadata for EPA PDF
    metadata = data["metadata"]
    assert "page_count" in metadata
    assert "file_size" in metadata
    assert "encrypted" in metadata
    assert metadata["page_count"] >= 1  # EPA sample should have at least 1 page
    assert not metadata["encrypted"]  # EPA sample should not be encrypted


def test_epa_sample_full_workflow(client: TestClient, epa_sample_pdf_content: bytes):
    """Test the complete workflow with EPA sample PDF."""
    # Upload EPA sample PDF
    files = {"file": ("epa_sample.pdf", io.BytesIO(epa_sample_pdf_content), "application/pdf")}
    upload_response = client.post("/api/upload", files=files)
    
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    file_id = upload_data["file_id"]
    
    # Retrieve the PDF file
    pdf_response = client.get(f"/api/pdf/{file_id}")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    
    # Verify the content matches what we uploaded
    assert len(pdf_response.content) == len(epa_sample_pdf_content)
    
    # Get metadata
    metadata_response = client.get(f"/api/metadata/{file_id}")
    assert metadata_response.status_code == 200
    metadata = metadata_response.json()
    
    # Verify EPA PDF specific properties
    assert metadata["page_count"] >= 1
    assert metadata["file_size"] > 1000
    assert not metadata["encrypted"]
    
    # Clean up
    delete_response = client.delete(f"/api/pdf/{file_id}")
    assert delete_response.status_code == 200


def test_epa_sample_large_file_handling(client: TestClient, epa_sample_pdf_content: bytes):
    """Test that EPA sample PDF is handled correctly even if it's larger."""
    # Verify the EPA sample is within our size limits
    file_size = len(epa_sample_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit
    
    assert file_size < max_size, f"EPA sample PDF ({file_size} bytes) exceeds size limit ({max_size} bytes)"
    
    # Upload and verify
    files = {"file": ("epa_sample.pdf", io.BytesIO(epa_sample_pdf_content), "application/pdf")}
    response = client.post("/api/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["file_size"] == file_size