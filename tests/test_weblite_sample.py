import io

import pytest
from fastapi.testclient import TestClient


def test_weblite_sample_upload_and_metadata(client: TestClient, weblite_sample_pdf_content: bytes):
    """Test uploading the Weblite OCR sample PDF and verifying its metadata."""
    files = {"file": ("weblite_sample.pdf", io.BytesIO(weblite_sample_pdf_content), "application/pdf")}
    
    response = client.post("/api/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "file_id" in data
    assert data["filename"] == "weblite_sample.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["file_size"] > 1000  # Weblite PDF should be reasonably sized
    
    # Check metadata for Weblite PDF
    metadata = data["metadata"]
    assert "page_count" in metadata
    assert "file_size" in metadata
    assert "encrypted" in metadata
    assert metadata["page_count"] >= 1  # Weblite sample should have at least 1 page
    assert not metadata["encrypted"]  # Weblite sample should not be encrypted


def test_weblite_sample_full_workflow(client: TestClient, weblite_sample_pdf_content: bytes):
    """Test the complete workflow with Weblite OCR sample PDF."""
    # Upload Weblite sample PDF
    files = {"file": ("weblite_sample.pdf", io.BytesIO(weblite_sample_pdf_content), "application/pdf")}
    upload_response = client.post("/api/upload", files=files)
    
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    file_id = upload_data["file_id"]
    
    # Retrieve the PDF file
    pdf_response = client.get(f"/api/pdf/{file_id}")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    
    # Verify the content matches what we uploaded
    assert len(pdf_response.content) == len(weblite_sample_pdf_content)
    
    # Get metadata
    metadata_response = client.get(f"/api/metadata/{file_id}")
    assert metadata_response.status_code == 200
    metadata = metadata_response.json()
    
    # Verify Weblite PDF specific properties
    assert metadata["page_count"] >= 1
    assert metadata["file_size"] > 1000
    assert not metadata["encrypted"]
    
    # Clean up
    delete_response = client.delete(f"/api/pdf/{file_id}")
    assert delete_response.status_code == 200


def test_weblite_sample_scanned_pdf_handling(client: TestClient, weblite_sample_pdf_content: bytes):
    """Test that Weblite scanned PDF sample is handled correctly."""
    # This PDF is specifically a scanned document sample, good for OCR testing
    files = {"file": ("weblite_sample.pdf", io.BytesIO(weblite_sample_pdf_content), "application/pdf")}
    response = client.post("/api/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify basic properties
    assert data["file_size"] > 0
    assert data["mime_type"] == "application/pdf"
    
    # Check that metadata extraction works for scanned PDFs
    metadata = data["metadata"]
    assert "page_count" in metadata
    assert "file_size" in metadata
    assert "encrypted" in metadata
    
    # Scanned PDFs should still have valid page counts
    assert metadata["page_count"] > 0


def test_multiple_pdf_samples_comparison(
    client: TestClient, 
    epa_sample_pdf_content: bytes, 
    weblite_sample_pdf_content: bytes
):
    """Test handling multiple different PDF samples to ensure system robustness."""
    # Upload EPA sample
    epa_files = {"file": ("epa_sample.pdf", io.BytesIO(epa_sample_pdf_content), "application/pdf")}
    epa_response = client.post("/api/upload", files=epa_files)
    assert epa_response.status_code == 200
    epa_data = epa_response.json()
    epa_file_id = epa_data["file_id"]
    
    # Upload Weblite sample
    weblite_files = {"file": ("weblite_sample.pdf", io.BytesIO(weblite_sample_pdf_content), "application/pdf")}
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
    assert epa_metadata["page_count"] > 0
    assert weblite_metadata["page_count"] > 0
    assert not epa_metadata["encrypted"]
    assert not weblite_metadata["encrypted"]
    
    # Clean up both files
    epa_delete_response = client.delete(f"/api/pdf/{epa_file_id}")
    weblite_delete_response = client.delete(f"/api/pdf/{weblite_file_id}")
    
    assert epa_delete_response.status_code == 200
    assert weblite_delete_response.status_code == 200