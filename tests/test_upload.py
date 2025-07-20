import io

from fastapi.testclient import TestClient


def test_upload_valid_pdf(client: TestClient, sample_pdf_content: bytes):
    """Test uploading a valid PDF file."""
    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}

    response = client.post("/api/upload", files=files)

    assert response.status_code == 200
    data = response.json()

    assert "file_id" in data
    assert "filename" in data
    assert "file_size" in data
    assert "mime_type" in data
    assert "upload_time" in data
    assert "metadata" in data

    assert data["filename"] == "test.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["file_size"] > 0

    # Check metadata
    metadata = data["metadata"]
    assert "page_count" in metadata
    assert "file_size" in metadata
    assert "encrypted" in metadata
    assert metadata["page_count"] > 0


def test_upload_invalid_file_type(client: TestClient):
    """Test uploading a non-PDF file."""
    files = {"file": ("test.txt", io.BytesIO(b"Not a PDF"), "text/plain")}

    response = client.post("/api/upload", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_upload_no_file(client: TestClient):
    """Test upload endpoint with no file."""
    response = client.post("/api/upload")

    assert response.status_code == 422  # Validation error


def test_upload_empty_filename(client: TestClient, sample_pdf_content: bytes):
    """Test uploading a file with no filename."""
    files = {"file": ("", io.BytesIO(sample_pdf_content), "application/pdf")}

    response = client.post("/api/upload", files=files)

    # FastAPI might return 422 for validation errors instead of 400
    assert response.status_code in [400, 422]
    data = response.json()
    if response.status_code == 400:
        assert (
            "filename" in data["detail"].lower()
            or "no filename" in data["detail"].lower()
        )
    else:
        # For 422, check validation error structure
        assert "detail" in data


def test_upload_large_file(client: TestClient):
    """Test uploading a file that exceeds size limit."""
    # Create a file larger than 50MB (the limit)
    large_content = b"x" * (51 * 1024 * 1024)  # 51MB
    files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}

    response = client.post("/api/upload", files=files)

    assert response.status_code == 413
    data = response.json()
    assert "too large" in data["detail"].lower()
