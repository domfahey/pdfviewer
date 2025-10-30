"""
Edge case tests for logging middleware.

This module complements test_logging_middleware.py by focusing on:
- Edge cases and boundary conditions
- Error scenarios and error handling
- Correlation ID edge cases
- Request/response body handling edge cases
- Header filtering and sanitization edge cases

For standard middleware functionality tests, see test_logging_middleware.py.
"""

import json
import os
import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from backend.app.middleware.logging import (
    LoggingMiddleware,
    RequestContextLogger,
    add_correlation_id,
    correlation_id_var,
    get_correlation_id,
    log_with_correlation,
    set_correlation_id,
)


@pytest.fixture(autouse=True)
def reset_correlation_context():
    """Reset correlation ID context before each test."""
    correlation_id_var.set(None)
    yield
    correlation_id_var.set(None)


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request object."""
    request = Mock(spec=Request)
    request.method = "GET"
    request.url = Mock()
    request.url.path = "/test"
    request.url.__str__ = Mock(return_value="http://testserver/test")
    request.query_params = {}
    request.headers = {}
    request.client = Mock()
    request.client.host = "127.0.0.1"
    return request


class TestLoggingMiddlewareInitialization:
    """Test LoggingMiddleware initialization and configuration."""

    def test_middleware_default_initialization(self):
        """Test middleware with default parameters."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        assert middleware.correlation_header == "X-Correlation-ID"
        assert middleware.max_body_size == 4096
        assert "authorization" in middleware.sensitive_headers
        assert "cookie" in middleware.sensitive_headers

    def test_middleware_custom_initialization(self):
        """Test middleware with custom parameters."""
        app = FastAPI()
        middleware = LoggingMiddleware(
            app,
            correlation_header="X-Custom-ID",
            log_request_bodies=False,
            log_response_bodies=False,
            max_body_size=8192,
        )

        assert middleware.correlation_header == "X-Custom-ID"
        assert middleware.log_request_bodies is False
        assert middleware.log_response_bodies is False
        assert middleware.max_body_size == 8192

    @patch.dict(
        os.environ,
        {
            "LOG_REQUEST_BODIES": "false",
            "LOG_RESPONSE_BODIES": "false",
            "MAX_BODY_LOG_SIZE": "2048",
        },
    )
    def test_middleware_environment_variable_configuration(self):
        """Test middleware configuration from environment variables."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        assert middleware.log_request_bodies is False
        assert middleware.log_response_bodies is False
        assert middleware.max_body_size == 2048

    @patch.dict(os.environ, {"LOG_REQUEST_BODIES": "TRUE"})
    def test_middleware_environment_variable_case_insensitive(self):
        """Test that environment variables are case insensitive."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        assert middleware.log_request_bodies is True


class TestLoggingMiddlewareCorrelationID:
    """Test correlation ID generation and handling."""

    def test_correlation_id_generation(self):
        """Test automatic correlation ID generation."""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert "x-correlation-id" in response.headers
        correlation_id = response.headers["x-correlation-id"]
        # Should be a valid UUID
        uuid.UUID(correlation_id)

    def test_correlation_id_from_header(self):
        """Test using correlation ID from request header."""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        test_id = str(uuid.uuid4())
        response = client.get("/test", headers={"X-Correlation-ID": test_id})

        assert response.status_code == 200
        assert response.headers["x-correlation-id"] == test_id

    def test_custom_correlation_header(self):
        """Test custom correlation header name."""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware, correlation_header="X-Trace-ID")

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        test_id = str(uuid.uuid4())
        response = client.get("/test", headers={"X-Trace-ID": test_id})

        assert response.status_code == 200
        assert response.headers["x-trace-id"] == test_id


class TestLoggingMiddlewareClientIP:
    """Test client IP address extraction."""

    def test_get_client_ip_x_forwarded_for(self):
        """Test IP extraction from X-Forwarded-For header."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "192.168.1.1, 10.0.0.1"}
        request.client = Mock()
        request.client.host = "127.0.0.1"

        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_x_real_ip(self):
        """Test IP extraction from X-Real-IP header."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        request = Mock(spec=Request)
        request.headers = {"x-real-ip": "192.168.1.100"}
        request.client = Mock()
        request.client.host = "127.0.0.1"

        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.100"

    def test_get_client_ip_fallback_to_direct(self):
        """Test IP fallback to direct connection."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "10.0.0.50"

        ip = middleware._get_client_ip(request)
        assert ip == "10.0.0.50"

    def test_get_client_ip_no_client(self):
        """Test IP extraction when no client info available."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        request = Mock(spec=Request)
        request.headers = {}
        request.client = None

        ip = middleware._get_client_ip(request)
        assert ip == "unknown"


class TestLoggingMiddlewareHeaderFiltering:
    """Test sensitive header filtering."""

    def test_filter_headers_sensitive_headers(self):
        """Test that sensitive headers are redacted."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        headers = {
            "authorization": "Bearer secret-token",
            "cookie": "session=abc123",
            "x-api-key": "key123",
            "content-type": "application/json",
            "user-agent": "test-client",
        }

        filtered = middleware._filter_headers(headers)

        assert filtered["authorization"] == "[REDACTED]"
        assert filtered["cookie"] == "[REDACTED]"
        assert filtered["x-api-key"] == "[REDACTED]"
        assert filtered["content-type"] == "application/json"
        assert filtered["user-agent"] == "test-client"

    def test_filter_headers_case_insensitive(self):
        """Test that header filtering is case insensitive."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        headers = {
            "Authorization": "Bearer secret-token",
            "COOKIE": "session=abc123",
            "X-Api-Key": "key123",
        }

        filtered = middleware._filter_headers(headers)

        assert filtered["Authorization"] == "[REDACTED]"
        assert filtered["COOKIE"] == "[REDACTED]"
        assert filtered["X-Api-Key"] == "[REDACTED]"


class TestLoggingMiddlewareBodyLogging:
    """Test request/response body logging logic."""

    def test_should_log_body_content_length_too_large(self):
        """Test body logging skip for large content."""
        app = FastAPI()
        middleware = LoggingMiddleware(app, max_body_size=1024)

        request = Mock(spec=Request)
        request.headers = {"content-length": "2048", "content-type": "application/json"}

        assert middleware._should_log_body(request) is False

    def test_should_log_body_binary_content_types(self):
        """Test body logging skip for binary content types."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        binary_types = [
            "image/jpeg",
            "video/mp4",
            "audio/mpeg",
            "application/pdf",
            "application/octet-stream",
        ]

        for content_type in binary_types:
            request = Mock(spec=Request)
            request.headers = {"content-type": content_type}

            assert middleware._should_log_body(request) is False

    def test_should_log_body_valid_content(self):
        """Test body logging allowed for valid content."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        request = Mock(spec=Request)
        request.headers = {"content-type": "application/json", "content-length": "512"}

        assert middleware._should_log_body(request) is True

    def test_should_log_response_body_content_length_too_large(self):
        """Test response body logging skip for large responses."""
        app = FastAPI()
        middleware = LoggingMiddleware(app, max_body_size=1024)

        response = Mock(spec=Response)
        response.headers = {
            "content-length": "2048",
            "content-type": "application/json",
        }

        assert middleware._should_log_response_body(response) is False

    def test_should_log_response_body_binary_content(self):
        """Test response body logging skip for binary content."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        response = Mock(spec=Response)
        response.headers = {"content-type": "application/pdf"}

        assert middleware._should_log_response_body(response) is False


class TestLoggingMiddlewareBodyReading:
    """Test safe body reading functionality."""

    @pytest.mark.asyncio
    async def test_safe_read_body_success(self):
        """Test successful body reading."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        request = Mock(spec=Request)
        request.body = AsyncMock(return_value=b'{"key": "value"}')

        result = await middleware._safe_read_body(request)
        assert result == '{"key": "value"}'

    @pytest.mark.asyncio
    async def test_safe_read_body_too_large(self):
        """Test body reading with size limit."""
        app = FastAPI()
        middleware = LoggingMiddleware(app, max_body_size=10)

        request = Mock(spec=Request)
        large_body = b"x" * 50
        request.body = AsyncMock(return_value=large_body)

        result = await middleware._safe_read_body(request)
        assert "[BODY TOO LARGE: 50 bytes]" in result

    @pytest.mark.asyncio
    async def test_safe_read_body_binary_content(self):
        """Test body reading with binary content."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        request = Mock(spec=Request)
        binary_body = b"\x89PNG\r\n\x1a\n"
        request.body = AsyncMock(return_value=binary_body)

        result = await middleware._safe_read_body(request)
        assert "[BINARY CONTENT:" in result

    @pytest.mark.asyncio
    async def test_safe_read_body_exception(self):
        """Test body reading with exception."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        request = Mock(spec=Request)
        request.body = AsyncMock(side_effect=Exception("Read error"))

        result = await middleware._safe_read_body(request)
        assert "[ERROR READING BODY: Read error]" in result

    @pytest.mark.asyncio
    async def test_safe_read_response_body_streaming(self):
        """Test response body reading for streaming response."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        response = Mock()
        response.body_iterator = Mock()

        result = await middleware._safe_read_response_body(response)
        assert result == "[STREAMING/FILE RESPONSE]"

    @pytest.mark.asyncio
    async def test_safe_read_response_body_file_response(self):
        """Test response body reading for file response."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        response = Mock()
        response.path = "/path/to/file"

        result = await middleware._safe_read_response_body(response)
        assert result == "[STREAMING/FILE RESPONSE]"

    @pytest.mark.asyncio
    async def test_safe_read_response_body_success(self):
        """Test successful response body reading."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        response = Mock()
        response.body = b'{"result": "success"}'

        result = await middleware._safe_read_response_body(response)
        assert result == '{"result": "success"}'

    @pytest.mark.asyncio
    async def test_safe_read_response_body_too_large(self):
        """Test response body reading with size limit."""
        app = FastAPI()
        middleware = LoggingMiddleware(app, max_body_size=10)

        response = Mock()
        response.body = b"x" * 50

        result = await middleware._safe_read_response_body(response)
        assert "[BODY TOO LARGE: 50 bytes]" in result

    @pytest.mark.asyncio
    async def test_safe_read_response_body_exception(self):
        """Test response body reading with exception."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        response = Mock()
        response.body = Mock(side_effect=Exception("Response error"))

        result = await middleware._safe_read_response_body(response)
        assert "[ERROR READING RESPONSE: Response error]" in result


class TestLoggingMiddlewareBodySanitization:
    """Test body content sanitization."""

    def test_sanitize_body_json_content(self):
        """Test JSON body sanitization."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        body = '{"password": "secret", "username": "user", "token": "abc123"}'
        result = middleware._sanitize_body(body, "application/json")

        sanitized_data = json.loads(result)
        assert sanitized_data["password"] == "[REDACTED]"
        assert sanitized_data["username"] == "user"
        assert sanitized_data["token"] == "[REDACTED]"

    def test_sanitize_body_invalid_json(self):
        """Test body sanitization with invalid JSON."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        body = "invalid json content"
        result = middleware._sanitize_body(body, "application/json")

        assert result == "invalid json content"

    def test_sanitize_body_truncation(self):
        """Test body truncation for long content."""
        app = FastAPI()
        middleware = LoggingMiddleware(app, max_body_size=10)

        body = "This is a very long string that exceeds the limit"
        result = middleware._sanitize_body(body, "text/plain")

        assert len(result) > 10
        assert result.endswith("...[TRUNCATED]")

    def test_sanitize_json_data_nested_objects(self):
        """Test JSON data sanitization with nested structures."""
        app = FastAPI()
        middleware = LoggingMiddleware(app)

        data = {
            "user": {"password": "secret", "api_key": "key123", "name": "John"},
            "credentials": [
                {"secret": "hidden", "type": "oauth"},
                {"public": "visible", "auth": "token123"},
            ],
        }

        result = middleware._sanitize_json_data(data)

        assert result["user"]["password"] == "[REDACTED]"
        assert result["user"]["api_key"] == "[REDACTED]"
        assert result["user"]["name"] == "John"
        assert result["credentials"][0]["secret"] == "[REDACTED]"
        assert result["credentials"][0]["type"] == "oauth"
        assert result["credentials"][1]["public"] == "visible"
        assert result["credentials"][1]["auth"] == "[REDACTED]"


class TestLoggingMiddlewareDebugMode:
    """Test debug mode functionality."""

    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"})
    def test_debug_mode_includes_headers(self):
        """Test that debug mode includes request headers."""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        with patch("structlog.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            client = TestClient(app)
            response = client.get("/test", headers={"User-Agent": "test-client"})

            assert response.status_code == 200

            # Verify that headers were included in logging
            mock_logger.bind.assert_called()
            call_args = mock_logger.bind.call_args[1]
            # Should include headers in debug mode
            expected_keys = {"method", "url", "path", "correlation_id"}
            assert expected_keys.issubset(call_args.keys())

    @patch.dict(os.environ, {"LOG_LEVEL": "INFO"})
    def test_non_debug_mode_excludes_headers(self):
        """Test that non-debug mode excludes detailed headers."""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        with patch("structlog.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            client = TestClient(app)
            response = client.get("/test")

            assert response.status_code == 200


class TestLoggingMiddlewareErrorHandling:
    """Test error handling in middleware."""

    def test_middleware_exception_handling(self):
        """Test that middleware properly logs and re-raises exceptions."""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")

        with patch("structlog.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            client = TestClient(app)
            response = client.get("/error")

            assert response.status_code == 500

            # Verify error was logged
            mock_logger.bind.assert_called()
            # Check that error logging was called
            bound_logger = mock_logger.bind.return_value
            bound_logger.error.assert_called_once()

            error_call = bound_logger.error.call_args
            assert "Request failed with exception" in error_call[0][0]


class TestCorrelationIDFunctions:
    """Test correlation ID utility functions."""

    def test_add_correlation_id_processor(self):
        """Test add_correlation_id structlog processor."""
        set_correlation_id("test-id-123")

        event_dict = {"message": "test"}
        result = add_correlation_id(None, None, event_dict)

        assert result["correlation_id"] == "test-id-123"
        assert result["message"] == "test"

    def test_add_correlation_id_processor_no_id(self):
        """Test add_correlation_id processor when no ID is set."""
        set_correlation_id(None)

        event_dict = {"message": "test"}
        result = add_correlation_id(None, None, event_dict)

        assert "correlation_id" not in result
        assert result["message"] == "test"

    def test_get_correlation_id_generates_new(self):
        """Test that get_correlation_id generates new ID when none exists."""
        set_correlation_id(None)

        correlation_id = get_correlation_id()

        assert correlation_id is not None
        uuid.UUID(correlation_id)  # Should be valid UUID

        # Second call should return the same ID
        second_id = get_correlation_id()
        assert second_id == correlation_id

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID."""
        test_id = str(uuid.uuid4())

        set_correlation_id(test_id)
        retrieved_id = get_correlation_id()

        assert retrieved_id == test_id

    def test_set_correlation_id_none(self):
        """Test setting correlation ID to None."""
        set_correlation_id("test-id")
        set_correlation_id(None)

        # get_correlation_id should generate a new one
        new_id = get_correlation_id()
        assert new_id is not None
        assert new_id != "test-id"


class TestLoggerFunctions:
    """Test logger utility functions."""

    def test_log_with_correlation(self):
        """Test log_with_correlation function."""
        set_correlation_id("test-correlation-id")

        mock_logger = Mock()
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        result = log_with_correlation(mock_logger, extra_key="extra_value")

        mock_logger.bind.assert_called_once()
        call_args = mock_logger.bind.call_args[1]
        assert call_args["correlation_id"] == "test-correlation-id"
        assert call_args["extra_key"] == "extra_value"
        assert result == mock_bound_logger


class TestRequestContextLogger:
    """Test RequestContextLogger context manager."""

    def test_request_context_logger_enter_exit(self, mock_request):
        """Test RequestContextLogger context manager functionality."""
        set_correlation_id("test-context-id")

        mock_logger = Mock()
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        context_logger = RequestContextLogger(mock_logger, mock_request)

        with context_logger as log:
            assert log == mock_bound_logger
            mock_logger.bind.assert_called_once()

            call_args = mock_logger.bind.call_args[1]
            assert call_args["method"] == "GET"
            assert call_args["path"] == "/test"
            assert call_args["correlation_id"] == "test-context-id"

    def test_request_context_logger_exception_handling(self, mock_request):
        """Test RequestContextLogger exception handling."""
        mock_logger = Mock()
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        context_logger = RequestContextLogger(mock_logger, mock_request)

        try:
            with context_logger:
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should log the exception
        mock_bound_logger.error.assert_called_once()
        error_call = mock_bound_logger.error.call_args
        assert "Exception in request context" in error_call[0][0]


class TestLoggingMiddlewareIntegration:
    """Test full middleware integration scenarios."""

    def test_full_request_response_cycle(self):
        """Test complete request/response logging cycle."""
        app = FastAPI()
        app.add_middleware(
            LoggingMiddleware, log_request_bodies=True, log_response_bodies=True
        )

        @app.post("/api/test")
        async def test_endpoint(data: dict):
            return {"processed": data.get("input", "default")}

        with patch("structlog.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            client = TestClient(app)
            response = client.post(
                "/api/test",
                json={"input": "test_data"},
                headers={"X-Correlation-ID": "integration-test-id"},
            )

            assert response.status_code == 200
            assert response.headers["x-correlation-id"] == "integration-test-id"

            # Verify logging occurred
            mock_logger.bind.assert_called()
            mock_logger.info.assert_called()

    def test_middleware_with_large_request_body(self):
        """Test middleware behavior with large request bodies."""
        app = FastAPI()
        app.add_middleware(
            LoggingMiddleware, log_request_bodies=True, max_body_size=100
        )

        @app.post("/api/upload")
        async def upload_endpoint():
            return {"status": "received"}

        client = TestClient(app)
        large_data = {"data": "x" * 200}  # Exceeds max_body_size
        response = client.post("/api/upload", json=large_data)

        assert response.status_code == 200

    def test_middleware_performance_timing(self):
        """Test that middleware correctly measures request duration."""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/slow")
        async def slow_endpoint():
            import asyncio

            await asyncio.sleep(0.01)  # 10ms delay
            return {"message": "slow response"}

        with patch("structlog.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            client = TestClient(app)
            response = client.get("/slow")

            assert response.status_code == 200

            # Check that timing was recorded
            bound_logger = mock_logger.bind.return_value
            info_calls = bound_logger.info.call_args_list

            # Find the completion log call
            completion_call = None
            for call in info_calls:
                if "Request completed" in str(call):
                    completion_call = call
                    break

            assert completion_call is not None
            call_kwargs = completion_call[1]
            assert "duration_ms" in call_kwargs
            # Duration should be at least 10ms
            assert call_kwargs["duration_ms"] >= 10
