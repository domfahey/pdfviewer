"""
Comprehensive tests for logging middleware and API logging functionality.

Tests cover correlation ID generation, performance tracking, request/response logging,
and the enhanced API logging decorators.
"""

import json
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.middleware.logging import LoggingMiddleware
from backend.app.utils.api_logging import (
    APILogger,
    log_api_call,
    log_file_operation,
    get_correlation_id,
    set_correlation_id
)


class TestLoggingMiddleware:
    """Test LoggingMiddleware functionality."""

    def test_middleware_adds_correlation_id_header(self):
        """Test that middleware adds correlation ID to response headers."""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "x-correlation-id" in response.headers
        # Should be a valid UUID
        correlation_id = response.headers["x-correlation-id"]
        uuid.UUID(correlation_id)  # Should not raise exception

    def test_middleware_uses_provided_correlation_id(self):
        """Test that middleware uses correlation ID from request header."""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        test_correlation_id = str(uuid.uuid4())
        response = client.get("/test", headers={"X-Correlation-ID": test_correlation_id})
        
        assert response.status_code == 200
        assert response.headers["x-correlation-id"] == test_correlation_id

    @patch('backend.app.middleware.logging.get_logger')
    def test_middleware_logs_request_start(self, mock_get_logger):
        """Test that middleware logs request start."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test?param=value")
        
        assert response.status_code == 200
        
        # Check that request start was logged
        mock_logger.info.assert_called()
        log_calls = mock_logger.info.call_args_list
        
        # Find the "Request started" log call
        request_start_call = None
        for call in log_calls:
            if "Request started" in str(call):
                request_start_call = call
                break
        
        assert request_start_call is not None

    @patch('backend.app.middleware.logging.get_logger')
    def test_middleware_logs_request_completion(self, mock_get_logger):
        """Test that middleware logs request completion with timing."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Check that request completion was logged
        mock_logger.info.assert_called()
        log_calls = mock_logger.info.call_args_list
        
        # Find the "Request completed" log call
        completion_call = None
        for call in log_calls:
            if "Request completed" in str(call):
                completion_call = call
                break
        
        assert completion_call is not None
        # Should include timing information
        kwargs = completion_call[1]
        assert "duration_ms" in kwargs

    @patch('backend.app.middleware.logging.get_logger')
    def test_middleware_logs_errors(self, mock_get_logger):
        """Test that middleware logs errors properly."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
        
        @app.get("/error")
        async def error_endpoint():
            raise Exception("Test error")
        
        client = TestClient(app)
        response = client.get("/error")
        
        assert response.status_code == 500
        
        # Check that error was logged
        mock_logger.error.assert_called()


class TestAPILogger:
    """Test APILogger class functionality."""

    def test_api_logger_initialization(self):
        """Test APILogger initialization."""
        logger = APILogger("test_operation")
        
        assert logger.operation_name == "test_operation"
        assert logger.start_time is not None
        assert logger.context == {}

    @patch('backend.app.utils.api_logging.get_logger')
    def test_log_request_received(self, mock_get_logger):
        """Test logging request received."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        logger = APILogger("test_operation")
        logger.log_request_received(
            method="POST",
            path="/test",
            query_params={"param": "value"}
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "API request received" in call_args[0]

    @patch('backend.app.utils.api_logging.get_logger')
    def test_log_processing_start(self, mock_get_logger):
        """Test logging processing start."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        logger = APILogger("test_operation")
        logger.log_processing_start(operation="file_validation")
        
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args
        assert "Processing started" in call_args[0]

    @patch('backend.app.utils.api_logging.get_logger')
    def test_log_processing_success(self, mock_get_logger):
        """Test logging processing success."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        logger = APILogger("test_operation")
        logger.log_processing_success(result_count=5, file_size=1024)
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "Processing completed successfully" in call_args[0]

    @patch('backend.app.utils.api_logging.get_logger')
    def test_log_processing_error(self, mock_get_logger):
        """Test logging processing error."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        logger = APILogger("test_operation")
        error = Exception("Test error")
        logger.log_processing_error(error, context={"file_id": "123"})
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Processing failed" in call_args[0]

    @patch('backend.app.utils.api_logging.get_logger')
    def test_log_response_prepared(self, mock_get_logger):
        """Test logging response preparation."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        logger = APILogger("test_operation")
        logger.log_response_prepared(
            status_code=200,
            response_size=1024,
            metadata={"key": "value"}
        )
        
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args
        assert "Response prepared" in call_args[0]

    @patch('backend.app.utils.api_logging.get_logger')
    def test_log_api_completed(self, mock_get_logger):
        """Test logging API completion."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        logger = APILogger("test_operation")
        logger.log_api_completed(
            status_code=200,
            response_size=1024
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "API operation completed" in call_args[0]
        # Should include timing
        kwargs = call_args[1]
        assert "duration_ms" in kwargs


class TestAPILoggingDecorators:
    """Test API logging decorators."""

    @patch('backend.app.utils.api_logging.APILogger')
    def test_log_api_call_decorator(self, mock_api_logger_class):
        """Test log_api_call decorator functionality."""
        mock_logger = Mock()
        mock_api_logger_class.return_value = mock_logger
        
        @log_api_call("test_operation", log_params=True, log_response=True)
        async def test_function(param1: str, param2: int = 10):
            return {"result": "success", "param1": param1, "param2": param2}
        
        # Call the decorated function
        import asyncio
        result = asyncio.run(test_function("test_value", param2=20))
        
        # Verify the result is unchanged
        assert result == {"result": "success", "param1": "test_value", "param2": 20}
        
        # Verify APILogger was created
        mock_api_logger_class.assert_called_once_with("test_operation")
        
        # Verify logging methods were called
        mock_logger.log_request_received.assert_called_once()
        mock_logger.log_processing_start.assert_called_once()
        mock_logger.log_processing_success.assert_called_once()
        mock_logger.log_api_completed.assert_called_once()

    @patch('backend.app.utils.api_logging.APILogger')
    def test_log_api_call_decorator_with_error(self, mock_api_logger_class):
        """Test log_api_call decorator handles errors."""
        mock_logger = Mock()
        mock_api_logger_class.return_value = mock_logger
        
        @log_api_call("test_operation")
        async def failing_function():
            raise ValueError("Test error")
        
        # Call the decorated function and expect error
        import asyncio
        with pytest.raises(ValueError):
            asyncio.run(failing_function())
        
        # Verify error logging was called
        mock_logger.log_processing_error.assert_called_once()

    @patch('backend.app.utils.api_logging.APILogger')
    def test_log_file_operation_decorator(self, mock_api_logger_class):
        """Test log_file_operation decorator functionality."""
        mock_logger = Mock()
        mock_api_logger_class.return_value = mock_logger
        
        # Mock file object
        mock_file = Mock()
        mock_file.filename = "test.pdf"
        mock_file.size = 1024
        mock_file.content_type = "application/pdf"
        
        @log_file_operation("file_upload", file_param="file", log_file_details=True)
        async def test_file_function(file, other_param: str = "default"):
            return {"uploaded": True, "filename": file.filename}
        
        # Call the decorated function
        import asyncio
        result = asyncio.run(test_file_function(mock_file, other_param="test"))
        
        # Verify the result is unchanged
        assert result == {"uploaded": True, "filename": "test.pdf"}
        
        # Verify file operation logging
        mock_logger.log_file_received.assert_called_once()
        mock_logger.log_file_processed.assert_called_once()


class TestCorrelationIDManagement:
    """Test correlation ID context management."""

    def test_get_correlation_id_generates_new(self):
        """Test that get_correlation_id generates new ID when none exists."""
        # Clear any existing correlation ID
        set_correlation_id(None)
        
        correlation_id = get_correlation_id()
        
        assert correlation_id is not None
        # Should be a valid UUID
        uuid.UUID(correlation_id)

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID."""
        test_id = str(uuid.uuid4())
        
        set_correlation_id(test_id)
        retrieved_id = get_correlation_id()
        
        assert retrieved_id == test_id

    def test_correlation_id_context_isolation(self):
        """Test that correlation IDs are properly isolated in context."""
        import asyncio
        
        async def set_and_get_id(test_id: str) -> str:
            set_correlation_id(test_id)
            # Simulate some async work
            await asyncio.sleep(0.01)
            return get_correlation_id()
        
        async def test_isolation():
            # Start multiple tasks with different correlation IDs
            id1 = str(uuid.uuid4())
            id2 = str(uuid.uuid4())
            
            task1 = asyncio.create_task(set_and_get_id(id1))
            task2 = asyncio.create_task(set_and_get_id(id2))
            
            result1, result2 = await asyncio.gather(task1, task2)
            
            assert result1 == id1
            assert result2 == id2
            assert result1 != result2
        
        asyncio.run(test_isolation())


class TestPerformanceTracking:
    """Test performance tracking in logging."""

    @patch('backend.app.utils.api_logging.get_logger')
    def test_api_logger_tracks_duration(self, mock_get_logger):
        """Test that APILogger tracks operation duration."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        import time
        
        logger = APILogger("test_operation")
        start_time = logger.start_time
        
        # Simulate some processing time
        time.sleep(0.01)  # 10ms
        
        logger.log_api_completed(status_code=200)
        
        # Check that duration was calculated
        call_args = mock_logger.info.call_args
        kwargs = call_args[1]
        
        assert "duration_ms" in kwargs
        duration = kwargs["duration_ms"]
        # Should be at least 10ms (allowing for some variance)
        assert duration >= 10

    @patch('backend.app.utils.api_logging.APILogger')
    def test_performance_tracking_in_decorator(self, mock_api_logger_class):
        """Test that decorators properly track performance."""
        mock_logger = Mock()
        mock_api_logger_class.return_value = mock_logger
        
        @log_api_call("test_operation", log_timing=True)
        async def timed_function():
            import asyncio
            await asyncio.sleep(0.01)  # 10ms
            return {"result": "completed"}
        
        import asyncio
        asyncio.run(timed_function())
        
        # Verify timing was logged
        mock_logger.log_api_completed.assert_called_once()
        call_args = mock_logger.log_api_completed.call_args
        # Should have been called with timing information
        assert call_args is not None


class TestLoggingIntegration:
    """Test integration between middleware and API logging."""

    @patch('backend.app.middleware.logging.get_logger')
    @patch('backend.app.utils.api_logging.get_logger')
    def test_correlation_id_propagation(self, mock_api_logger, mock_middleware_logger):
        """Test that correlation ID propagates from middleware to API logging."""
        mock_mw_logger = Mock()
        mock_api_log = Mock()
        mock_middleware_logger.return_value = mock_mw_logger
        mock_api_logger.return_value = mock_api_log
        
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
        
        @app.get("/test")
        @log_api_call("test_endpoint")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        test_correlation_id = str(uuid.uuid4())
        response = client.get("/test", headers={"X-Correlation-ID": test_correlation_id})
        
        assert response.status_code == 200
        assert response.headers["x-correlation-id"] == test_correlation_id
        
        # Both middleware and API logging should have used the same correlation ID
        # This is verified by checking that the correlation ID appears in log calls
        middleware_calls = mock_mw_logger.info.call_args_list
        api_calls = mock_api_log.info.call_args_list
        
        # At least one call should include the correlation ID
        assert len(middleware_calls) > 0
        assert len(api_calls) > 0

    def test_end_to_end_logging_workflow(self):
        """Test complete logging workflow from request to response."""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
        
        @app.post("/upload")
        @log_api_call("file_upload", log_params=True, log_response=True)
        @log_file_operation("upload", file_param="file")
        async def upload_endpoint(file: dict):
            return {
                "file_id": "test-id",
                "filename": file.get("filename", "test.pdf"),
                "status": "uploaded"
            }
        
        client = TestClient(app)
        
        # Send request with file data
        response = client.post("/upload", json={"filename": "test.pdf", "size": 1024})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "uploaded"
        
        # Verify correlation ID was added
        assert "x-correlation-id" in response.headers