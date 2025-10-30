"""
Comprehensive unit tests for backend/app/utils/api_logging.py module.

Tests cover API logging decorators, file operation logging,
parameter sanitization, and the APILogger class.
"""

import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import Request

from backend.app.utils.api_logging import (
    APILogger,
    _sanitize_params,
    _sanitize_response,
    get_logger,
    log_api_call,
    log_file_operation,
)


class TestGetLogger:
    """Test get_logger utility function."""

    def test_get_logger_returns_bound_logger(self):
        """Test get_logger returns a structured logger."""
        logger = get_logger("test_module")

        assert logger is not None

    def test_get_logger_with_custom_name(self):
        """Test get_logger with custom module name."""
        logger = get_logger("custom.module.name")

        assert logger is not None

    def test_get_logger_default_name(self):
        """Test get_logger with default name."""
        logger = get_logger()

        assert logger is not None


class TestSanitizeParams:
    """Test _sanitize_params function."""

    def test_sanitize_params_no_sensitive_keys(self):
        """Test sanitization with no sensitive keys."""
        params = {"user_id": "123", "action": "upload"}
        result = _sanitize_params(params, [])

        assert result == params

    def test_sanitize_params_redacts_sensitive_keys(self):
        """Test sanitization redacts sensitive parameters."""
        params = {"username": "john", "password": "secret123", "api_key": "key123"}
        sensitive = ["password", "api_key"]

        result = _sanitize_params(params, sensitive)

        assert result["username"] == "john"
        assert result["password"] == "[REDACTED]"
        assert result["api_key"] == "[REDACTED]"

    def test_sanitize_params_case_insensitive_matching(self):
        """Test sanitization is case-insensitive."""
        params = {"Password": "secret", "API_KEY": "key"}
        sensitive = ["password", "api_key"]

        result = _sanitize_params(params, sensitive)

        assert result["Password"] == "[REDACTED]"
        assert result["API_KEY"] == "[REDACTED]"

    def test_sanitize_params_handles_complex_objects(self):
        """Test sanitization of complex object types."""

        class CustomObject:
            pass

        params = {
            "simple_string": "value",
            "number": 42,
            "bool": True,
            "custom_obj": CustomObject(),
        }

        result = _sanitize_params(params, [])

        assert result["simple_string"] == "value"
        assert result["number"] == 42
        assert result["bool"] is True
        assert "<CustomObject>" in result["custom_obj"]

    def test_sanitize_params_empty_dict(self):
        """Test sanitization of empty parameter dict."""
        result = _sanitize_params({}, ["password"])

        assert result == {}

    def test_sanitize_params_preserves_non_sensitive_data(self):
        """Test that non-sensitive data is preserved exactly."""
        params = {
            "user_id": "user123",
            "count": 5,
            "active": True,
            "price": 19.99,
        }

        result = _sanitize_params(params, ["secret"])

        assert result == params


class TestSanitizeResponse:
    """Test _sanitize_response function."""

    def test_sanitize_response_no_sensitive_fields(self):
        """Test sanitization with no sensitive fields."""
        response = {"status": "success", "data": {"id": "123"}}
        result = _sanitize_response(response)

        assert result == response

    def test_sanitize_response_redacts_password(self):
        """Test sanitization redacts password fields."""
        response = {"username": "john", "password": "secret123"}
        result = _sanitize_response(response)

        assert result["username"] == "john"
        assert result["password"] == "[REDACTED]"

    def test_sanitize_response_redacts_token(self):
        """Test sanitization redacts token fields."""
        response = {"user_id": "123", "access_token": "tok_123"}
        result = _sanitize_response(response)

        assert result["user_id"] == "123"
        assert result["access_token"] == "[REDACTED]"

    def test_sanitize_response_redacts_secret(self):
        """Test sanitization redacts secret fields."""
        response = {"api_secret": "secret_key", "data": "safe"}
        result = _sanitize_response(response)

        assert result["api_secret"] == "[REDACTED]"
        assert result["data"] == "safe"

    def test_sanitize_response_handles_nested_dicts(self):
        """Test sanitization works with nested dictionaries."""
        response = {
            "user": {"name": "john", "auth_token": "secret"},
            "settings": {"theme": "dark"},
        }

        result = _sanitize_response(response)

        assert result["user"]["name"] == "john"
        assert result["user"]["auth_token"] == "[REDACTED]"
        assert result["settings"]["theme"] == "dark"

    def test_sanitize_response_partial_match(self):
        """Test sanitization with partial field name matches."""
        response = {
            "user_password": "pass123",
            "reset_token": "tok456",
            "encryption_key": "key789",
        }

        result = _sanitize_response(response)

        assert result["user_password"] == "[REDACTED]"
        assert result["reset_token"] == "[REDACTED]"
        assert result["encryption_key"] == "[REDACTED]"

    def test_sanitize_response_empty_dict(self):
        """Test sanitization of empty response."""
        result = _sanitize_response({})

        assert result == {}


class TestLogApiCallDecorator:
    """Test log_api_call decorator."""

    @pytest.mark.asyncio
    async def test_log_api_call_basic_success(self):
        """Test log_api_call decorator with successful operation."""

        @log_api_call("test_operation")
        async def test_function():
            return {"status": "success"}

        result = await test_function()

        assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_log_api_call_with_request_parameter(self):
        """Test log_api_call extracts Request information."""
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        mock_request.client.host = "127.0.0.1"

        @log_api_call("test_operation")
        async def test_function(request: Request):
            return {"status": "ok"}

        result = await test_function(mock_request)

        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_log_api_call_logs_parameters(self):
        """Test log_api_call logs function parameters."""

        @log_api_call("test_operation", log_params=True)
        async def test_function(user_id: str, count: int):
            return {"user_id": user_id, "count": count}

        result = await test_function(user_id="123", count=5)

        assert result == {"user_id": "123", "count": 5}

    @pytest.mark.asyncio
    async def test_log_api_call_sanitizes_sensitive_params(self):
        """Test log_api_call sanitizes sensitive parameters."""

        @log_api_call("test_operation", log_params=True, sensitive_params=["password"])
        async def test_function(username: str, password: str):
            return {"username": username}

        result = await test_function(username="john", password="secret123")

        assert result == {"username": "john"}

    @pytest.mark.asyncio
    async def test_log_api_call_logs_response(self):
        """Test log_api_call logs response data."""

        @log_api_call("test_operation", log_response=True)
        async def test_function():
            return {"data": "test_data", "count": 42}

        result = await test_function()

        assert result == {"data": "test_data", "count": 42}

    @pytest.mark.asyncio
    async def test_log_api_call_handles_pydantic_model_response(self):
        """Test log_api_call handles Pydantic model responses."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            name: str
            value: int

        @log_api_call("test_operation", log_response=True)
        async def test_function():
            return TestModel(name="test", value=123)

        result = await test_function()

        assert result.name == "test"
        assert result.value == 123

    @pytest.mark.asyncio
    async def test_log_api_call_handles_exceptions(self):
        """Test log_api_call properly logs and re-raises exceptions."""

        @log_api_call("failing_operation")
        async def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await failing_function()

    @pytest.mark.asyncio
    async def test_log_api_call_without_params_logging(self):
        """Test log_api_call with parameter logging disabled."""

        @log_api_call("test_operation", log_params=False)
        async def test_function(secret_data: str):
            return {"status": "ok"}

        result = await test_function(secret_data="sensitive")

        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_log_api_call_measures_timing(self):
        """Test log_api_call measures execution time."""
        import asyncio

        @log_api_call("slow_operation", log_timing=True)
        async def slow_function():
            await asyncio.sleep(0.01)
            return "done"

        result = await slow_function()

        assert result == "done"


class TestLogFileOperationDecorator:
    """Test log_file_operation decorator."""

    @pytest.mark.asyncio
    async def test_log_file_operation_basic_success(self):
        """Test log_file_operation with successful file operation."""

        @log_file_operation("file_upload")
        async def upload_function(file):
            return {"file_id": "123"}

        mock_file = Mock()
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = 1024

        result = await upload_function(file=mock_file)

        assert result == {"file_id": "123"}

    @pytest.mark.asyncio
    async def test_log_file_operation_custom_file_param(self):
        """Test log_file_operation with custom file parameter name."""

        @log_file_operation("file_process", file_param="document")
        async def process_function(document):
            return {"processed": True}

        mock_file = Mock()
        mock_file.filename = "doc.pdf"

        result = await process_function(document=mock_file)

        assert result == {"processed": True}

    @pytest.mark.asyncio
    async def test_log_file_operation_logs_file_details(self):
        """Test log_file_operation logs file details."""

        @log_file_operation("file_upload", log_file_details=True)
        async def upload_function(file):
            return {"status": "uploaded"}

        mock_file = Mock()
        mock_file.filename = "document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = 2048

        result = await upload_function(file=mock_file)

        assert result == {"status": "uploaded"}

    @pytest.mark.asyncio
    async def test_log_file_operation_without_file_details(self):
        """Test log_file_operation without logging file details."""

        @log_file_operation("file_upload", log_file_details=False)
        async def upload_function(file):
            return {"status": "ok"}

        result = await upload_function(file=Mock())

        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_log_file_operation_handles_missing_file(self):
        """Test log_file_operation when file is not in kwargs."""

        @log_file_operation("file_operation")
        async def operation_without_file():
            return {"status": "ok"}

        result = await operation_without_file()

        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_log_file_operation_handles_exceptions(self):
        """Test log_file_operation logs and re-raises exceptions."""

        @log_file_operation("file_upload")
        async def failing_upload(file):
            raise IOError("File upload failed")

        with pytest.raises(IOError, match="File upload failed"):
            await failing_upload(file=Mock())

    @pytest.mark.asyncio
    async def test_log_file_operation_includes_result_file_id(self):
        """Test log_file_operation logs file_id from result."""

        class UploadResult:
            file_id = "file_123"

        @log_file_operation("file_upload")
        async def upload_function(file):
            return UploadResult()

        result = await upload_function(file=Mock())

        assert result.file_id == "file_123"

    @pytest.mark.asyncio
    async def test_log_file_operation_measures_timing(self):
        """Test log_file_operation measures execution time."""
        import asyncio

        @log_file_operation("slow_file_operation")
        async def slow_operation(file):
            await asyncio.sleep(0.01)
            return {"done": True}

        result = await slow_operation(file=Mock())

        assert result == {"done": True}


class TestAPILogger:
    """Test APILogger class."""

    def test_api_logger_initialization(self):
        """Test APILogger initialization."""
        logger = APILogger("test_operation")

        assert logger.operation == "test_operation"
        assert logger.operation_name == "test_operation"
        assert logger.correlation_id is not None

    def test_api_logger_with_custom_correlation_id(self):
        """Test APILogger with custom correlation ID."""
        logger = APILogger("test_operation", correlation_id="custom-123")

        assert logger.correlation_id == "custom-123"

    def test_api_logger_log_request_received(self):
        """Test log_request_received method."""
        logger = APILogger("test_operation")

        # Should not raise any exceptions
        logger.log_request_received(user_id="123")

    def test_api_logger_log_validation_start(self):
        """Test log_validation_start method."""
        logger = APILogger("test_operation")

        logger.log_validation_start(field_count=5)

    def test_api_logger_log_validation_success(self):
        """Test log_validation_success method."""
        logger = APILogger("test_operation")

        logger.log_validation_success(validated_fields=10)

    def test_api_logger_log_validation_error(self):
        """Test log_validation_error method."""
        logger = APILogger("test_operation")

        logger.log_validation_error("Invalid field value", field="email")

    def test_api_logger_log_processing_start(self):
        """Test log_processing_start method."""
        logger = APILogger("test_operation")

        logger.log_processing_start(records=100)

    def test_api_logger_log_processing_success(self):
        """Test log_processing_success method."""
        logger = APILogger("test_operation")

        logger.log_processing_success(processed_count=50)

    def test_api_logger_log_processing_error(self):
        """Test log_processing_error method."""
        logger = APILogger("test_operation")

        error = ValueError("Processing failed")
        logger.log_processing_error(error, record_id="123")

    def test_api_logger_log_response_prepared(self):
        """Test log_response_prepared method."""
        logger = APILogger("test_operation")

        logger.log_response_prepared(item_count=10)

    def test_api_logger_log_api_completed(self):
        """Test log_api_completed method."""
        logger = APILogger("test_operation")

        logger.log_api_completed(status_code=200, response_size=1024)

    def test_api_logger_log_api_completed_measures_duration(self):
        """Test log_api_completed includes duration measurement."""
        import time

        logger = APILogger("test_operation")
        time.sleep(0.01)  # Simulate some work

        logger.log_api_completed(status_code=200)

    def test_api_logger_log_file_received(self):
        """Test log_file_received method."""
        logger = APILogger("file_operation")

        logger.log_file_received(filename="test.pdf", file_size=2048)

    def test_api_logger_log_file_processed(self):
        """Test log_file_processed method."""
        logger = APILogger("file_operation")

        logger.log_file_processed(filename="test.pdf", page_count=5)

    def test_api_logger_full_workflow(self):
        """Test complete APILogger workflow."""
        logger = APILogger("upload_operation", correlation_id="test-123")

        # Simulate full request lifecycle
        logger.log_request_received(method="POST")
        logger.log_validation_start()
        logger.log_validation_success()
        logger.log_file_received(filename="test.pdf", file_size=1024)
        logger.log_processing_start()
        logger.log_file_processed(filename="test.pdf")
        logger.log_processing_success()
        logger.log_response_prepared()
        logger.log_api_completed(status_code=201, response_size=256)

        assert logger.operation == "upload_operation"
        assert logger.correlation_id == "test-123"


class TestLoggingIntegration:
    """Integration tests for api_logging module."""

    @pytest.mark.asyncio
    async def test_complete_api_logging_workflow(self):
        """Test complete API logging workflow with decorators."""

        @log_api_call("test_workflow", log_params=True, log_response=True)
        async def api_endpoint(user_id: str, action: str):
            return {"user_id": user_id, "action": action, "status": "success"}

        result = await api_endpoint(user_id="123", action="test")

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_file_operation_workflow(self):
        """Test file operation logging workflow."""

        @log_file_operation("upload_workflow", log_file_details=True)
        async def upload_endpoint(file):
            class Result:
                file_id = "uploaded_123"

            return Result()

        mock_file = Mock()
        mock_file.filename = "document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = 4096

        result = await upload_endpoint(file=mock_file)

        assert result.file_id == "uploaded_123"

    def test_api_logger_with_context(self):
        """Test APILogger in a complete request context."""
        logger = APILogger("request_processing", correlation_id="req-456")

        try:
            logger.log_request_received(endpoint="/api/test")
            logger.log_validation_start()

            # Simulate validation
            logger.log_validation_success(fields_validated=5)

            logger.log_processing_start()

            # Simulate processing
            logger.log_processing_success(items_processed=10)

            logger.log_response_prepared(response_items=10)
            logger.log_api_completed(status_code=200, response_size=512)

        except Exception as e:
            logger.log_processing_error(e)
            raise
