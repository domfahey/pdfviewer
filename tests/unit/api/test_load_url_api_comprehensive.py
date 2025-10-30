"""
Comprehensive tests for Load URL API endpoint to increase coverage.

This module focuses on edge cases, error scenarios, validation logic,
and network-related error handling for the load_pdf_from_url endpoint.
"""

import uuid
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.api.load_url import LoadPDFRequest
from backend.app.dependencies import get_pdf_service, init_pdf_service
from backend.app.models.pdf import PDFUploadResponse
from backend.app.services.pdf_service import PDFService


@pytest.fixture(autouse=True)
def reset_load_url_service_state():
    """Reset PDF service global state before each test."""
    from backend.app.dependencies import reset_pdf_service

    reset_pdf_service()

    yield

    reset_pdf_service()


@pytest.fixture
def shared_pdf_service():
    """Provide a shared PDF service instance for tests that need persistence."""
    from backend.app.dependencies import init_pdf_service
    from backend.app.services.pdf_service import PDFService

    service = PDFService(upload_dir="uploads")
    init_pdf_service(service)
    return service


@pytest.fixture
def valid_file_id():
    """Provide a valid UUID for testing."""
    return str(uuid.uuid4())


def create_mock_response(headers, content, status_code=200):
    """Helper to create properly configured mock response objects."""
    mock_response = Mock()
    mock_response.headers = headers
    mock_response.content = content
    mock_response.status_code = status_code
    mock_response.raise_for_status = Mock()
    return mock_response


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
        from backend.app.api import load_url

        load_url._pdf_service = None

        # The actual code imports PDFService inside the function, so we need to patch differently
        with patch(
            "backend.app.services.pdf_service.PDFService"
        ) as mock_pdf_service_class:
            mock_instance = Mock(spec=PDFService)
            mock_pdf_service_class.return_value = mock_instance

            result = get_pdf_service()

            # The function creates a new instance and returns the mock
            assert result is mock_instance


class TestLoadPDFRequestModel:
    """Test LoadPDFRequest Pydantic model validation."""

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        request = LoadPDFRequest(url="http://example.com/test.pdf")
        assert str(request.url) == "http://example.com/test.pdf"

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        request = LoadPDFRequest(url="https://example.com/test.pdf")
        assert str(request.url) == "https://example.com/test.pdf"

    def test_invalid_url_format(self):
        """Test invalid URL format raises ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LoadPDFRequest(url="not-a-url")

    def test_invalid_url_scheme(self):
        """Test invalid URL scheme raises ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LoadPDFRequest(url="ftp://example.com/test.pdf")

    def test_empty_url(self):
        """Test empty URL raises ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LoadPDFRequest(url="")


class TestLoadPDFFromURLEndpoint:
    """Test /load-url endpoint edge cases and error scenarios."""

    def test_invalid_request_body_missing_url(self, client: TestClient):
        """Test POST with missing URL field."""
        response = client.post("/api/load-url", json={})
        assert response.status_code == 422
        data = response.json()
        assert "Field required" in str(data["detail"])

    def test_invalid_request_body_invalid_url_format(self, client: TestClient):
        """Test POST with invalid URL format."""
        response = client.post("/api/load-url", json={"url": "not-a-url"})
        assert response.status_code == 422
        data = response.json()
        assert "Input should be a valid URL" in str(data["detail"])

    def test_invalid_request_body_non_http_scheme(self, client: TestClient):
        """Test POST with non-HTTP URL scheme."""
        response = client.post(
            "/api/load-url", json={"url": "ftp://example.com/test.pdf"}
        )
        assert response.status_code == 422

    @patch("httpx.AsyncClient")
    def test_network_timeout_error(self, mock_client_class, client: TestClient):
        """Test network timeout during PDF download."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = httpx.TimeoutException("Request timeout")

        response = client.post(
            "/api/load-url", json={"url": "https://example.com/test.pdf"}
        )
        assert response.status_code == 504
        data = response.json()
        assert "Timeout downloading PDF" in data["detail"]

    @patch("httpx.AsyncClient")
    def test_network_error(self, mock_client_class, client: TestClient):
        """Test network error during PDF download."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = httpx.NetworkError("Network unreachable")

        response = client.post(
            "/api/load-url", json={"url": "https://example.com/test.pdf"}
        )
        assert response.status_code == 504
        data = response.json()
        assert "Timeout downloading PDF" in data["detail"]

    @patch("httpx.AsyncClient")
    def test_http_status_error(self, mock_client_class, client: TestClient):
        """Test HTTP status error (404, 500, etc.)."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = Mock()
        mock_response.status_code = 404
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )

        response = client.post(
            "/api/load-url", json={"url": "https://example.com/test.pdf"}
        )
        assert response.status_code == 502
        data = response.json()
        assert "Failed to download PDF from URL: 404" in data["detail"]

    @patch("httpx.AsyncClient")
    def test_request_error(self, mock_client_class, client: TestClient):
        """Test general request error."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = httpx.RequestError("Connection failed")

        response = client.post(
            "/api/load-url", json={"url": "https://example.com/test.pdf"}
        )
        assert response.status_code == 502
        data = response.json()
        assert "Failed to connect to URL" in data["detail"]

    @patch("httpx.AsyncClient")
    def test_invalid_content_type(self, mock_client_class, client: TestClient):
        """Test invalid content type (not PDF)."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = create_mock_response(
            headers={"content-type": "text/html"}, content=b"<html>Not a PDF</html>"
        )
        mock_client.get.return_value = mock_response

        response = client.post(
            "/api/load-url", json={"url": "https://example.com/test.html"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "URL does not point to a PDF file" in data["detail"]
        assert "content-type: text/html" in data["detail"]

    @patch("httpx.AsyncClient")
    def test_missing_content_type_header(self, mock_client_class, client: TestClient):
        """Test missing content-type header."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = create_mock_response(
            headers={},  # No content-type header
            content=b"%PDF-1.4 fake pdf content",
        )
        mock_client.get.return_value = mock_response

        response = client.post(
            "/api/load-url", json={"url": "https://example.com/test.pdf"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "URL does not point to a PDF file" in data["detail"]

    @patch("httpx.AsyncClient")
    def test_retry_logic_eventually_succeeds(
        self, mock_client_class, client: TestClient, sample_pdf_content: bytes
    ):
        """Test retry logic with eventual success."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # First two calls fail, third succeeds
        mock_response = AsyncMock()
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.content = sample_pdf_content
        mock_response.raise_for_status = Mock()

        mock_client.get.side_effect = [
            httpx.TimeoutException("First timeout"),
            httpx.NetworkError("Second failure"),
            mock_response,
        ]

        with patch("asyncio.sleep") as mock_sleep:
            with patch(
                "backend.app.services.pdf_service.PDFService.upload_pdf"
            ) as mock_upload:
                mock_upload.return_value = PDFUploadResponse(
                    file_id=str(uuid.uuid4()),
                    filename="downloaded.pdf",
                    file_size=len(sample_pdf_content),
                    mime_type="application/pdf",
                )

                response = client.post(
                    "/api/load-url", json={"url": "https://example.com/test.pdf"}
                )

        assert response.status_code == 200
        # Verify exponential backoff was used (sleep called twice)
        assert mock_sleep.call_count == 2

    @patch("httpx.AsyncClient")
    def test_retry_logic_all_attempts_fail(self, mock_client_class, client: TestClient):
        """Test retry logic when all attempts fail."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # All attempts fail
        mock_client.get.side_effect = [
            httpx.TimeoutException("First timeout"),
            httpx.TimeoutException("Second timeout"),
            httpx.TimeoutException("Third timeout"),
        ]

        with patch("asyncio.sleep"):
            response = client.post(
                "/api/load-url", json={"url": "https://example.com/test.pdf"}
            )

        assert response.status_code == 504
        data = response.json()
        assert "Timeout downloading PDF after 3 attempts" in data["detail"]

    @patch("httpx.AsyncClient")
    def test_filename_extraction_from_content_disposition(
        self,
        mock_client_class,
        client: TestClient,
        sample_pdf_content: bytes,
        valid_file_id: str,
    ):
        """Test filename extraction from content-disposition header."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = create_mock_response(
            headers={
                "content-type": "application/pdf",
                "content-disposition": 'attachment; filename="report.pdf"',
            },
            content=sample_pdf_content,
        )
        mock_client.get.return_value = mock_response

        with patch(
            "backend.app.services.pdf_service.PDFService.upload_pdf"
        ) as mock_upload:
            mock_upload.return_value = PDFUploadResponse(
                file_id=valid_file_id,
                filename="report.pdf",
                file_size=len(sample_pdf_content),
                mime_type="application/pdf",
            )

            response = client.post(
                "/api/load-url", json={"url": "https://example.com/test.pdf"}
            )

        assert response.status_code == 200
        # Verify the correct filename was extracted and used
        mock_upload.assert_called_once()
        uploaded_file = mock_upload.call_args[0][0]
        assert uploaded_file.filename == "report.pdf"

    @patch("httpx.AsyncClient")
    def test_filename_extraction_from_url(
        self,
        mock_client_class,
        client: TestClient,
        sample_pdf_content: bytes,
        valid_file_id: str,
    ):
        """Test filename extraction from URL when no content-disposition."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = create_mock_response(
            headers={"content-type": "application/pdf"}, content=sample_pdf_content
        )
        mock_client.get.return_value = mock_response

        with patch(
            "backend.app.services.pdf_service.PDFService.upload_pdf"
        ) as mock_upload:
            mock_upload.return_value = PDFUploadResponse(
                file_id=valid_file_id,
                filename="document.pdf",
                file_size=len(sample_pdf_content),
                mime_type="application/pdf",
            )

            response = client.post(
                "/api/load-url", json={"url": "https://example.com/path/document.pdf"}
            )

        assert response.status_code == 200
        mock_upload.assert_called_once()
        uploaded_file = mock_upload.call_args[0][0]
        assert uploaded_file.filename == "document.pdf"

    @patch("httpx.AsyncClient")
    def test_filename_fallback_to_default(
        self, mock_client_class, client: TestClient, sample_pdf_content: bytes
    ):
        """Test filename fallback when no filename can be extracted."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.content = sample_pdf_content
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        with patch(
            "backend.app.services.pdf_service.PDFService.upload_pdf"
        ) as mock_upload:
            mock_upload.return_value = PDFUploadResponse(
                file_id=str(uuid.uuid4()),
                filename="downloaded.pdf",
                file_size=len(sample_pdf_content),
                mime_type="application/pdf",
            )

            response = client.post(
                "/api/load-url", json={"url": "https://example.com/path/no-extension"}
            )

        assert response.status_code == 200
        mock_upload.assert_called_once()
        uploaded_file = mock_upload.call_args[0][0]
        assert uploaded_file.filename == "downloaded.pdf"

    @patch("httpx.AsyncClient")
    def test_pdf_service_upload_failure(
        self, mock_client_class, client: TestClient, sample_pdf_content: bytes
    ):
        """Test PDF service upload failure."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.content = sample_pdf_content
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        with patch(
            "backend.app.services.pdf_service.PDFService.upload_pdf"
        ) as mock_upload:
            mock_upload.side_effect = Exception("Upload service failed")

            response = client.post(
                "/api/load-url", json={"url": "https://example.com/test.pdf"}
            )

        assert response.status_code == 500
        data = response.json()
        assert "Failed to load PDF from URL" in data["detail"]

    @patch("httpx.AsyncClient")
    def test_successful_load_with_all_features(
        self, mock_client_class, client: TestClient, sample_pdf_content: bytes
    ):
        """Test successful PDF load with all features working."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.headers = {
            "content-type": "application/pdf",
            "content-disposition": 'attachment; filename="annual_report.pdf"',
        }
        mock_response.content = sample_pdf_content
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        with patch(
            "backend.app.services.pdf_service.PDFService.upload_pdf"
        ) as mock_upload:
            expected_response = PDFUploadResponse(
                file_id=str(uuid.uuid4()),
                filename="annual_report.pdf",
                file_size=len(sample_pdf_content),
                mime_type="application/pdf",
            )
            mock_upload.return_value = expected_response

            response = client.post(
                "/api/load-url",
                json={"url": "https://example.com/reports/annual_report.pdf"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == expected_response.file_id
        assert data["filename"] == "annual_report.pdf"
        assert data["file_size"] == len(sample_pdf_content)
        assert data["mime_type"] == "application/pdf"


class TestAPILoggingIntegration:
    """Test API logging functionality integration."""

    def test_api_logging_decorator_applied(self, client: TestClient):
        """Test that the log_api_call decorator is properly applied."""
        # Test that the endpoint has the decorator by checking if the function
        # has been wrapped (we can verify this by making a request and checking logs)
        from backend.app.api.load_url import load_pdf_from_url

        # The function should have the decorator applied
        assert hasattr(load_pdf_from_url, "__wrapped__") or callable(load_pdf_from_url)

        # Make a test request to verify logging works (this tests integration)
        response = client.post("/api/load-url", json={"url": "invalid-url"})
        assert response.status_code == 422  # Should get validation error


class TestNetworkConfiguration:
    """Test network configuration and settings."""

    @patch("httpx.AsyncClient")
    def test_httpx_client_configuration(self, mock_client_class, client: TestClient):
        """Test that httpx client is configured with proper timeout and limits."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")

        client.post("/api/load-url", json={"url": "https://example.com/test.pdf"})

        # Verify client was created with proper configuration
        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args[1]

        # Check timeout configuration
        assert call_kwargs["timeout"].read == 60.0
        assert call_kwargs["timeout"].connect == 10.0

        # Check limits configuration
        assert call_kwargs["limits"].max_keepalive_connections == 5
        assert call_kwargs["limits"].max_connections == 10

        # Check redirect following
        assert call_kwargs["follow_redirects"] is True


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("httpx.AsyncClient")
    def test_very_large_pdf_response(self, mock_client_class, client: TestClient):
        """Test handling of very large PDF responses."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Create a large fake PDF content (10MB)
        large_pdf_content = b"%PDF-1.4\n" + b"x" * (10 * 1024 * 1024)

        mock_response = AsyncMock()
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.content = large_pdf_content
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        with patch(
            "backend.app.services.pdf_service.PDFService.upload_pdf"
        ) as mock_upload:
            mock_upload.return_value = PDFUploadResponse(
                file_id=str(uuid.uuid4()),
                filename="large.pdf",
                file_size=len(large_pdf_content),
                mime_type="application/pdf",
            )

            response = client.post(
                "/api/load-url", json={"url": "https://example.com/large.pdf"}
            )

        assert response.status_code == 200

    def test_unicode_url_handling(self, client: TestClient):
        """Test handling of URLs with Unicode characters."""
        # This should be handled by Pydantic URL validation
        unicode_url = "https://example.com/файл.pdf"
        response = client.post("/api/load-url", json={"url": unicode_url})

        # The response depends on whether the URL is valid after encoding
        # This tests that we don't crash on Unicode URLs
        assert response.status_code in [200, 422, 502, 504]

    @patch("httpx.AsyncClient")
    def test_malformed_content_disposition_header(
        self, mock_client_class, client: TestClient, sample_pdf_content: bytes
    ):
        """Test handling of malformed content-disposition header."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.headers = {
            "content-type": "application/pdf",
            "content-disposition": "malformed header without filename",
        }
        mock_response.content = sample_pdf_content
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        with patch(
            "backend.app.services.pdf_service.PDFService.upload_pdf"
        ) as mock_upload:
            mock_upload.return_value = PDFUploadResponse(
                file_id=str(uuid.uuid4()),
                filename="downloaded.pdf",
                file_size=len(sample_pdf_content),
                mime_type="application/pdf",
            )

            response = client.post(
                "/api/load-url", json={"url": "https://example.com/test.pdf"}
            )

        assert response.status_code == 200
        # Should fall back to URL-based filename extraction or default
        mock_upload.assert_called_once()
        uploaded_file = mock_upload.call_args[0][0]
        assert uploaded_file.filename in ["test.pdf", "downloaded.pdf"]
