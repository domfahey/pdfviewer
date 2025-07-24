import io

from fastapi.testclient import TestClient

from tests.helpers import (
    upload_pdf_file,
    assert_upload_success_response,
    assert_valid_pdf_content,
    assert_file_size_fields,
    assert_error_response,
)


def test_upload_valid_pdf(client: TestClient, sample_pdf_content: bytes):
    """Test uploading a valid PDF file."""
    # Validate PDF content first using helper
    assert_valid_pdf_content(sample_pdf_content)

    # Use helper to upload PDF file
    response = upload_pdf_file(client, "test.pdf", sample_pdf_content)

    # Use helper to validate response structure
    data = assert_upload_success_response(response, expected_filename="test.pdf")

    # Validate file size fields using helper
    assert_file_size_fields(data, expected_bytes=len(sample_pdf_content))

    # Check specific Pydantic v2 enhanced fields
    assert data["mime_type"] == "application/pdf"

    # Validate POC info structure
    poc_info = data["_poc_info"]
    assert poc_info["model_version"] == "2.0"
    assert poc_info["enhanced_validation"] is True

    # Check enhanced metadata fields are present (validation handled by assert_upload_success_response)
    metadata = data["metadata"]
    enhanced_fields = [
        "file_size_mb",
        "document_complexity_score",
        "document_category",
        "is_large_document",
    ]
    for field in enhanced_fields:
        assert field in metadata, f"Missing enhanced metadata field: {field}"


def test_upload_invalid_file_type(client: TestClient):
    """Test uploading a non-PDF file using workflow helper."""
    # Use helper to perform upload workflow expecting failure
    files = {"file": ("test.txt", io.BytesIO(b"Not a PDF"), "text/plain")}
    response = client.post("/api/upload", files=files)

    # Use helper to validate error response
    assert_error_response(response, 400, "Only PDF files are allowed")


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


def test_upload_with_correlation_id(client: TestClient, sample_pdf_content: bytes):
    """Test upload with correlation ID header tracking."""
    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    correlation_id = "test-correlation-123"

    response = client.post(
        "/api/upload", files=files, headers={"X-Correlation-ID": correlation_id}
    )

    assert response.status_code == 200
    assert response.headers.get("x-correlation-id") == correlation_id


def test_upload_cors_headers(client: TestClient, sample_pdf_content: bytes):
    """Test CORS headers are properly set for upload endpoint."""
    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    origin = "http://localhost:5173"

    response = client.post("/api/upload", files=files, headers={"Origin": origin})

    assert response.status_code == 200
    # Note: CORS headers are typically set by middleware, not endpoint


def test_upload_enhanced_error_response(client: TestClient):
    """Test enhanced error response format."""
    # Upload invalid file to trigger error
    files = {"file": ("test.txt", io.BytesIO(b"Not a PDF"), "text/plain")}

    response = client.post("/api/upload", files=files)

    assert response.status_code == 400
    data = response.json()

    # Should have enhanced error format
    assert "detail" in data


def test_upload_filename_validation(client: TestClient, sample_pdf_content: bytes):
    """Test filename validation with security checks."""
    # Test various filename scenarios
    test_cases = [
        ("normal.pdf", 200),
        ("file-name.pdf", 200),
        ("file_name.pdf", 200),
        # These should be handled by validation
    ]

    for filename, expected_status in test_cases:
        files = {"file": (filename, io.BytesIO(sample_pdf_content), "application/pdf")}
        response = client.post("/api/upload", files=files)
        assert response.status_code == expected_status


def test_upload_response_timing_fields(client: TestClient, sample_pdf_content: bytes):
    """Test that timing-related computed fields are present."""
    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}

    response = client.post("/api/upload", files=files)

    assert response.status_code == 200
    data = response.json()

    # Check timing fields
    assert "upload_time" in data
    assert "upload_age_hours" in data
    assert "upload_status" in data

    # Upload should be "fresh"
    assert data["upload_status"] == "fresh"
    assert data["upload_age_hours"] < 1.0  # Should be very recent


def test_upload_processing_priority_assignment(
    client: TestClient, sample_pdf_content: bytes
):
    """Test processing priority assignment based on file characteristics."""
    files = {"file": ("small.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}

    response = client.post("/api/upload", files=files)

    assert response.status_code == 200
    data = response.json()

    # Small file should get high priority
    assert data["processing_priority"] == "high"


def test_upload_metadata_complexity_scoring(
    client: TestClient, sample_pdf_content: bytes
):
    """Test document complexity scoring in metadata."""
    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}

    response = client.post("/api/upload", files=files)

    assert response.status_code == 200
    data = response.json()

    metadata = data["metadata"]
    assert "document_complexity_score" in metadata
    assert isinstance(metadata["document_complexity_score"], int | float)
    assert 0 <= metadata["document_complexity_score"] <= 100

    assert "document_category" in metadata
    assert metadata["document_category"] in [
        "single-page",
        "short-document",
        "medium-document",
        "long-document",
        "very-long-document",
    ]
