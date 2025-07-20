import io

import pytest
from fastapi.testclient import TestClient


def test_princexml_sample_upload_and_metadata(client: TestClient, princexml_sample_pdf_content: bytes):
    """Test uploading the PrinceXML large essay PDF and verifying its metadata."""
    files = {"file": ("princexml_essay.pdf", io.BytesIO(princexml_sample_pdf_content), "application/pdf")}
    
    response = client.post("/api/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "file_id" in data
    assert data["filename"] == "princexml_essay.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["file_size"] > 10000  # PrinceXML essay should be a substantial file
    
    # Check metadata for PrinceXML PDF
    metadata = data["metadata"]
    assert "page_count" in metadata
    assert "file_size" in metadata
    assert "encrypted" in metadata
    assert metadata["page_count"] >= 1  # Essay should have multiple pages
    assert not metadata["encrypted"]  # Essay should not be encrypted


def test_princexml_sample_large_file_handling(client: TestClient, princexml_sample_pdf_content: bytes):
    """Test that PrinceXML large PDF is handled correctly within size limits."""
    file_size = len(princexml_sample_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit
    
    # Log the actual file size for debugging
    print(f"PrinceXML PDF size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    
    # If the file is too large, test that it's properly rejected
    if file_size >= max_size:
        files = {"file": ("princexml_essay.pdf", io.BytesIO(princexml_sample_pdf_content), "application/pdf")}
        response = client.post("/api/upload", files=files)
        assert response.status_code == 413  # File too large
        data = response.json()
        assert "too large" in data["detail"].lower()
    else:
        # If within limits, test successful upload
        files = {"file": ("princexml_essay.pdf", io.BytesIO(princexml_sample_pdf_content), "application/pdf")}
        response = client.post("/api/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["file_size"] == file_size


def test_princexml_sample_full_workflow(client: TestClient, princexml_sample_pdf_content: bytes):
    """Test the complete workflow with PrinceXML essay PDF if within size limits."""
    file_size = len(princexml_sample_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit
    
    # Skip if file is too large for our current limits
    if file_size >= max_size:
        pytest.skip(f"PrinceXML PDF ({file_size:,} bytes) exceeds 50MB limit - testing size rejection instead")
    
    # Upload PrinceXML essay PDF
    files = {"file": ("princexml_essay.pdf", io.BytesIO(princexml_sample_pdf_content), "application/pdf")}
    upload_response = client.post("/api/upload", files=files)
    
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    file_id = upload_data["file_id"]
    
    # Retrieve the PDF file
    pdf_response = client.get(f"/api/pdf/{file_id}")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    
    # Verify the content matches what we uploaded
    assert len(pdf_response.content) == len(princexml_sample_pdf_content)
    
    # Get metadata
    metadata_response = client.get(f"/api/metadata/{file_id}")
    assert metadata_response.status_code == 200
    metadata = metadata_response.json()
    
    # Verify PrinceXML PDF specific properties
    assert metadata["page_count"] >= 1
    assert metadata["file_size"] > 10000
    assert not metadata["encrypted"]
    
    # Clean up
    delete_response = client.delete(f"/api/pdf/{file_id}")
    assert delete_response.status_code == 200


def test_princexml_sample_performance(client: TestClient, princexml_sample_pdf_content: bytes):
    """Test performance characteristics with larger PDF file."""
    import time
    
    file_size = len(princexml_sample_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit
    
    # Skip if file is too large
    if file_size >= max_size:
        pytest.skip(f"PrinceXML PDF ({file_size:,} bytes) exceeds 50MB limit")
    
    files = {"file": ("princexml_essay.pdf", io.BytesIO(princexml_sample_pdf_content), "application/pdf")}
    
    # Time the upload process
    start_time = time.time()
    response = client.post("/api/upload", files=files)
    upload_time = time.time() - start_time
    
    assert response.status_code == 200
    data = response.json()
    file_id = data["file_id"]
    
    # Upload should complete in reasonable time (adjust threshold as needed)
    assert upload_time < 30.0, f"Upload took {upload_time:.2f} seconds, which may be too slow"
    
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
    
    # Log performance metrics
    print(f"Performance metrics for {file_size:,} byte PDF:")
    print(f"  Upload: {upload_time:.2f}s")
    print(f"  Metadata: {metadata_time:.2f}s") 
    print(f"  Retrieval: {retrieval_time:.2f}s")


def test_multiple_pdf_samples_with_large_file(
    client: TestClient, 
    epa_sample_pdf_content: bytes, 
    weblite_sample_pdf_content: bytes,
    princexml_sample_pdf_content: bytes
):
    """Test handling multiple PDF samples including a larger file."""
    princexml_size = len(princexml_sample_pdf_content)
    max_size = 50 * 1024 * 1024  # 50MB limit
    
    # Upload smaller samples first
    epa_files = {"file": ("epa_sample.pdf", io.BytesIO(epa_sample_pdf_content), "application/pdf")}
    epa_response = client.post("/api/upload", files=epa_files)
    assert epa_response.status_code == 200
    epa_file_id = epa_response.json()["file_id"]
    
    weblite_files = {"file": ("weblite_sample.pdf", io.BytesIO(weblite_sample_pdf_content), "application/pdf")}
    weblite_response = client.post("/api/upload", files=weblite_files)
    assert weblite_response.status_code == 200
    weblite_file_id = weblite_response.json()["file_id"]
    
    # Try to upload PrinceXML sample
    princexml_files = {"file": ("princexml_essay.pdf", io.BytesIO(princexml_sample_pdf_content), "application/pdf")}
    princexml_response = client.post("/api/upload", files=princexml_files)
    
    if princexml_size >= max_size:
        # Should be rejected for size
        assert princexml_response.status_code == 413
        princexml_file_id = None
    else:
        # Should be accepted
        assert princexml_response.status_code == 200
        princexml_file_id = princexml_response.json()["file_id"]
        
        # Verify all three files have different IDs
        assert len({epa_file_id, weblite_file_id, princexml_file_id}) == 3
        
        # Verify all can be retrieved
        princexml_pdf_response = client.get(f"/api/pdf/{princexml_file_id}")
        assert princexml_pdf_response.status_code == 200
    
    # Verify smaller files still work
    epa_pdf_response = client.get(f"/api/pdf/{epa_file_id}")
    weblite_pdf_response = client.get(f"/api/pdf/{weblite_file_id}")
    
    assert epa_pdf_response.status_code == 200
    assert weblite_pdf_response.status_code == 200
    
    # Clean up all files
    client.delete(f"/api/pdf/{epa_file_id}")
    client.delete(f"/api/pdf/{weblite_file_id}")
    if princexml_file_id:
        client.delete(f"/api/pdf/{princexml_file_id}")