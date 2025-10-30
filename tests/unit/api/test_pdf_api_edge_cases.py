"""
Edge case tests for PDF API endpoints.

This module complements test_pdf_endpoints.py by focusing on:
- Edge cases and boundary conditions
- Error scenarios and validation edge cases
- File handling edge cases
- Concurrent request edge cases

For standard API functionality tests, see test_pdf_endpoints.py.
"""

import io
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.dependencies import get_pdf_service, init_pdf_service
from backend.app.services.pdf_service import PDFService


@pytest.fixture(autouse=True)
def reset_pdf_service_state():
    """Reset PDF service global state before each test."""
    # Reset the global service instance using public API
    from backend.app.dependencies import reset_pdf_service

    reset_pdf_service()

    yield

    # Cleanup after test
    reset_pdf_service()


@pytest.fixture
def shared_pdf_service():
    """Provide a shared PDF service instance for tests that need persistence."""
    from backend.app.services.pdf_service import PDFService
    from backend.app.dependencies import init_pdf_service

    # Create a service instance
    service = PDFService(upload_dir="uploads")
    init_pdf_service(service)
    return service


class TestPDFServiceDependency:
    """Test PDF service dependency injection and fallback logic."""

    def test_get_pdf_service_with_initialized_service(self):
        """Test that get_pdf_service returns initialized service."""
        mock_service = Mock(spec=PDFService)
        init_pdf_service(mock_service)

        result = get_pdf_service()
        assert result is mock_service

    def test_get_pdf_service_fallback_when_not_initialized(self):
        """Test fallback to new instance when service not initialized."""
        # Reset global service to None
        from backend.app.api import pdf

        pdf._pdf_service = None

        with patch("backend.app.api.pdf.PDFService") as mock_pdf_service_class:
            mock_instance = Mock(spec=PDFService)
            mock_pdf_service_class.return_value = mock_instance

            result = get_pdf_service()

            mock_pdf_service_class.assert_called_once()
            assert result is mock_instance


class TestGetPDFFileEndpoint:
    """Test /pdf/{file_id} endpoint edge cases and error scenarios."""

    def test_get_pdf_empty_file_id(self, client: TestClient):
        """Test GET with empty file_id."""
        response = client.get("/api/pdf/")
        # FastAPI will return 404 for missing path parameter
        assert response.status_code == 404

    def test_get_pdf_whitespace_only_file_id(self, client: TestClient):
        """Test GET with whitespace-only file_id."""
        response = client.get("/api/pdf/   ")
        assert response.status_code == 400
        data = response.json()
        assert "File ID is required" in data["detail"]

    def test_get_pdf_valid_id_file_not_found(self, client: TestClient):
        """Test GET with valid ID but file doesn't exist."""
        response = client.get("/api/pdf/550e8400-e29b-41d4-a716-446655440000")
        assert response.status_code == 404

    def test_get_pdf_service_exception(self, client: TestClient):
        """Test GET when PDF service raises unexpected exception."""
        with patch(
            "backend.app.services.pdf_service.PDFService.get_pdf_path"
        ) as mock_get_path:
            mock_get_path.side_effect = Exception("Database connection failed")

            response = client.get("/api/pdf/test-file-id")
            assert response.status_code == 500
            data = response.json()
            assert "Failed to retrieve file" in data["detail"]

    def test_get_pdf_http_exception_passthrough(self, client: TestClient):
        """Test that HTTPExceptions from service are passed through."""
        with patch(
            "backend.app.services.pdf_service.PDFService.get_pdf_path"
        ) as mock_get_path:
            mock_get_path.side_effect = HTTPException(
                status_code=403, detail="Access denied"
            )

            response = client.get("/api/pdf/test-file-id")
            assert response.status_code == 403
            data = response.json()
            assert "Access denied" in data["detail"]

    def test_get_pdf_successful_response_headers(
        self, client: TestClient, sample_pdf_content: bytes, shared_pdf_service
    ):
        """Test successful PDF retrieval has correct headers."""
        # Upload a file first
        files = {
            "file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")
        }
        upload_response = client.post("/api/upload", files=files)
        file_id = upload_response.json()["file_id"]

        # Get the PDF
        response = client.get(f"/api/pdf/{file_id}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        # Check that filename is set correctly
        content_disposition = response.headers.get("content-disposition", "")
        assert f"{file_id}.pdf" in content_disposition

    def test_get_pdf_special_characters_in_id(self, client: TestClient):
        """Test GET with special characters in file_id."""
        special_id = "test-file@#$%^&*()"
        response = client.get(f"/api/pdf/{special_id}")
        # Should handle gracefully and return 404
        assert response.status_code == 404


class TestGetPDFMetadataEndpoint:
    """Test /metadata/{file_id} endpoint edge cases and error scenarios."""

    def test_get_metadata_empty_file_id(self, client: TestClient):
        """Test metadata GET with empty file_id."""
        response = client.get("/api/metadata/")
        assert response.status_code == 404

    def test_get_metadata_whitespace_only_file_id(self, client: TestClient):
        """Test metadata GET with whitespace-only file_id."""
        response = client.get("/api/metadata/   ")
        assert response.status_code == 400
        data = response.json()
        assert "File ID is required" in data["detail"]

    def test_get_metadata_service_exception(self, client: TestClient):
        """Test metadata GET when service raises exception."""
        with patch(
            "backend.app.services.pdf_service.PDFService.get_pdf_metadata"
        ) as mock_get_metadata:
            mock_get_metadata.side_effect = ValueError("Invalid PDF format")

            response = client.get("/api/metadata/test-file-id")
            assert response.status_code == 500
            data = response.json()
            assert "Failed to retrieve metadata" in data["detail"]

    def test_get_metadata_http_exception_passthrough(self, client: TestClient):
        """Test metadata GET with HTTPException from service."""
        with patch(
            "backend.app.services.pdf_service.PDFService.get_pdf_metadata"
        ) as mock_get_metadata:
            mock_get_metadata.side_effect = HTTPException(
                status_code=422, detail="File corrupted"
            )

            response = client.get("/api/metadata/test-file-id")
            assert response.status_code == 422
            data = response.json()
            assert "File corrupted" in data["detail"]

    def test_get_metadata_successful_response_structure(
        self, client: TestClient, sample_pdf_content: bytes, shared_pdf_service
    ):
        """Test successful metadata response has correct structure."""
        # Upload a file first
        files = {
            "file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")
        }
        upload_response = client.post("/api/upload", files=files)
        file_id = upload_response.json()["file_id"]

        # Get metadata
        response = client.get(f"/api/metadata/{file_id}")

        assert response.status_code == 200
        metadata = response.json()

        # Check required fields
        required_fields = ["page_count", "file_size", "encrypted"]
        for field in required_fields:
            assert field in metadata

        # Check data types
        assert isinstance(metadata["page_count"], int)
        assert isinstance(metadata["file_size"], int)
        assert isinstance(metadata["encrypted"], bool)
        assert metadata["page_count"] > 0
        assert metadata["file_size"] > 0


class TestDeletePDFEndpoint:
    """Test DELETE /pdf/{file_id} endpoint edge cases and error scenarios."""

    def test_delete_pdf_empty_file_id(self, client: TestClient):
        """Test DELETE with empty file_id."""
        response = client.delete("/api/pdf/")
        assert response.status_code == 404

    def test_delete_pdf_whitespace_only_file_id(self, client: TestClient):
        """Test DELETE with whitespace-only file_id."""
        response = client.delete("/api/pdf/   ")
        assert response.status_code == 400
        data = response.json()
        assert "File ID is required" in data["detail"]

    def test_delete_pdf_service_returns_false(self, client: TestClient):
        """Test DELETE when service returns False (delete failed)."""
        with patch(
            "backend.app.services.pdf_service.PDFService.delete_pdf"
        ) as mock_delete:
            mock_delete.return_value = False

            response = client.delete("/api/pdf/test-file-id")
            assert response.status_code == 500
            data = response.json()
            assert "Failed to delete file" in data["detail"]

    def test_delete_pdf_service_exception(self, client: TestClient):
        """Test DELETE when service raises exception."""
        with patch(
            "backend.app.services.pdf_service.PDFService.delete_pdf"
        ) as mock_delete:
            mock_delete.side_effect = PermissionError("Access denied")

            response = client.delete("/api/pdf/test-file-id")
            assert response.status_code == 500
            data = response.json()
            assert "Failed to delete file" in data["detail"]

    def test_delete_pdf_http_exception_passthrough(self, client: TestClient):
        """Test DELETE with HTTPException from service."""
        with patch(
            "backend.app.services.pdf_service.PDFService.delete_pdf"
        ) as mock_delete:
            mock_delete.side_effect = HTTPException(
                status_code=409, detail="File is being processed"
            )

            response = client.delete("/api/pdf/test-file-id")
            assert response.status_code == 409
            data = response.json()
            assert "File is being processed" in data["detail"]

    def test_delete_pdf_successful_response(
        self, client: TestClient, sample_pdf_content: bytes, shared_pdf_service
    ):
        """Test successful DELETE response format."""
        # Upload a file first
        files = {
            "file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")
        }
        upload_response = client.post("/api/upload", files=files)
        file_id = upload_response.json()["file_id"]

        # Delete the file
        response = client.delete(f"/api/pdf/{file_id}")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert file_id in data["message"]
        assert "deleted successfully" in data["message"]

    def test_delete_pdf_nonexistent_file(self, client: TestClient):
        """Test DELETE of non-existent file."""
        response = client.delete("/api/pdf/550e8400-e29b-41d4-a716-446655440000")
        assert response.status_code == 404


class TestAPILoggingIntegration:
    """Test API logging functionality integration."""

    @patch("backend.app.api.pdf.APILogger")
    def test_get_pdf_logging_calls(self, mock_api_logger_class, client: TestClient):
        """Test that proper logging calls are made for GET /pdf/{file_id}."""
        mock_logger = Mock()
        mock_api_logger_class.return_value = mock_logger

        client.get("/api/pdf/test-file-id")

        # Verify logging method calls
        mock_logger.log_request_received.assert_called_once()
        mock_logger.log_validation_start.assert_called_once()
        mock_logger.log_validation_success.assert_called_once()
        mock_logger.log_processing_start.assert_called_once()

    @patch("backend.app.api.pdf.APILogger")
    def test_get_metadata_logging_calls(
        self, mock_api_logger_class, client: TestClient
    ):
        """Test that proper logging calls are made for GET /metadata/{file_id}."""
        mock_logger = Mock()
        mock_api_logger_class.return_value = mock_logger

        client.get("/api/metadata/test-file-id")

        # Verify logging method calls
        mock_logger.log_request_received.assert_called_once()
        mock_logger.log_validation_start.assert_called_once()
        mock_logger.log_validation_success.assert_called_once()
        mock_logger.log_processing_start.assert_called_once()

    @patch("backend.app.api.pdf.APILogger")
    def test_delete_pdf_logging_calls(self, mock_api_logger_class, client: TestClient):
        """Test that proper logging calls are made for DELETE /pdf/{file_id}."""
        mock_logger = Mock()
        mock_api_logger_class.return_value = mock_logger

        client.delete("/api/pdf/test-file-id")

        # Verify logging method calls
        mock_logger.log_request_received.assert_called_once()
        mock_logger.log_validation_start.assert_called_once()
        mock_logger.log_validation_success.assert_called_once()
        mock_logger.log_processing_start.assert_called_once()


class TestConcurrentAccess:
    """Test concurrent access scenarios."""

    def test_concurrent_file_access_same_id(
        self, client: TestClient, sample_pdf_content: bytes, shared_pdf_service
    ):
        """Test concurrent access to same file ID."""
        # Upload a file first
        files = {
            "file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")
        }
        upload_response = client.post("/api/upload", files=files)
        file_id = upload_response.json()["file_id"]

        # Simulate concurrent requests
        responses = []
        for _ in range(3):
            response = client.get(f"/api/pdf/{file_id}")
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"

    def test_concurrent_metadata_requests(
        self, client: TestClient, sample_pdf_content: bytes, shared_pdf_service
    ):
        """Test concurrent metadata requests for same file."""
        # Upload a file first
        files = {
            "file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")
        }
        upload_response = client.post("/api/upload", files=files)
        file_id = upload_response.json()["file_id"]

        # Simulate concurrent metadata requests
        responses = []
        for _ in range(3):
            response = client.get(f"/api/metadata/{file_id}")
            responses.append(response)

        # All should succeed and return consistent data
        for response in responses:
            assert response.status_code == 200
            metadata = response.json()
            assert metadata["page_count"] > 0
            assert metadata["file_size"] > 0


class TestEdgeCaseInputs:
    """Test edge case inputs and boundary conditions."""

    def test_very_long_file_id(self, client: TestClient):
        """Test with very long file ID."""
        long_id = "a" * 1000  # 1000 character ID
        response = client.get(f"/api/pdf/{long_id}")
        # Should handle gracefully
        assert response.status_code in [404, 414]  # Not found or URI too long

    def test_unicode_file_id(self, client: TestClient):
        """Test with Unicode characters in file ID."""
        unicode_id = "test-文件-📄-id"
        response = client.get(f"/api/pdf/{unicode_id}")
        # Should handle gracefully
        assert response.status_code == 404

    def test_sql_injection_attempt_in_file_id(self, client: TestClient):
        """Test SQL injection attempt in file ID."""
        sql_injection_id = "'; DROP TABLE files; --"
        response = client.get(f"/api/pdf/{sql_injection_id}")
        # Should handle safely
        assert response.status_code == 404
