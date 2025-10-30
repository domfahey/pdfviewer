"""
Edge case tests for logging utilities.

This module provides additional coverage for logger utilities:
- Performance tracking edge cases
- Structured logging edge cases  
- Context binding edge cases
- Error logging edge cases
- Async logging edge cases

For standard logging functionality, see test_core_logging.py.
"""

import asyncio
import time
from unittest.mock import Mock, patch

import pytest

from backend.app.utils.logger import (
    FileOperationLogger,
    PerformanceTracker,
    log_dict_safely,
    log_exception_context,
    log_function_call,
)


class TestPerformanceTracker:
    """Test PerformanceTracker class functionality."""

    def test_performance_tracker_initialization_defaults(self):
        """Test PerformanceTracker with default parameters."""
        tracker = PerformanceTracker("test_operation")

        assert tracker.operation_name == "test_operation"
        assert tracker.log_start is True
        assert tracker.min_duration_ms == 0.0
        assert tracker.context == {}
        assert tracker.start_time is None
        assert tracker.end_time is None
        assert tracker.duration_ms is None

    def test_performance_tracker_initialization_custom(self):
        """Test PerformanceTracker with custom parameters."""
        mock_logger = Mock()
        tracker = PerformanceTracker(
            "custom_operation",
            logger_instance=mock_logger,
            log_start=False,
            min_duration_ms=100.0,
            custom_key="custom_value",
        )

        assert tracker.operation_name == "custom_operation"
        assert tracker.logger is mock_logger
        assert tracker.log_start is False
        assert tracker.min_duration_ms == 100.0
        assert tracker.context["custom_key"] == "custom_value"

    def test_performance_tracker_start_with_logging(self):
        """Test start method with logging enabled."""
        mock_logger = Mock()
        tracker = PerformanceTracker(
            "test_op", logger_instance=mock_logger, log_start=True
        )

        tracker.start()

        assert tracker.start_time is not None
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "Starting test_op" in call_args[0][0]

    def test_performance_tracker_start_without_logging(self):
        """Test start method with logging disabled."""
        mock_logger = Mock()
        tracker = PerformanceTracker(
            "test_op", logger_instance=mock_logger, log_start=False
        )

        tracker.start()

        assert tracker.start_time is not None
        mock_logger.info.assert_not_called()

    def test_performance_tracker_stop_success(self):
        """Test stop method for successful operation."""
        mock_logger = Mock()
        tracker = PerformanceTracker("test_op", logger_instance=mock_logger)

        tracker.start()
        time.sleep(0.01)  # 10ms delay
        duration = tracker.stop()

        assert duration >= 10  # At least 10ms
        assert tracker.end_time is not None

        # Should log completion
        mock_logger.info.assert_called()
        info_call = None
        for call in mock_logger.info.call_args_list:
            if "Completed test_op" in str(call):
                info_call = call
                break

        assert info_call is not None
        call_kwargs = info_call[1]
        assert call_kwargs["success"] is True
        assert call_kwargs["duration_ms"] >= 10

    def test_performance_tracker_stop_with_exception(self):
        """Test stop method with exception."""
        mock_logger = Mock()
        tracker = PerformanceTracker("test_op", logger_instance=mock_logger)

        tracker.start()
        time.sleep(0.01)
        duration = tracker.stop(exception=True, error="Test error")

        assert duration >= 10

        # Should log error
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args
        assert "Failed test_op" in error_call[0][0]
        assert error_call[1]["success"] is False
        assert error_call[1]["error"] == "Test error"

    def test_performance_tracker_stop_without_start_raises_error(self):
        """Test that stop without start raises RuntimeError."""
        tracker = PerformanceTracker("test_op")

        with pytest.raises(RuntimeError) as exc_info:
            tracker.stop()

        assert "must be called before stop()" in str(exc_info.value)

    def test_performance_tracker_min_duration_threshold(self):
        """Test minimum duration threshold filtering."""
        mock_logger = Mock()
        tracker = PerformanceTracker(
            "test_op", logger_instance=mock_logger, min_duration_ms=50.0
        )

        tracker.start()
        # Very short operation (less than 50ms)
        time.sleep(0.001)  # 1ms
        duration = tracker.stop()

        # Should still return duration
        assert duration >= 1

        # But should not log because below threshold
        mock_logger.info.assert_called_once()  # Only the start log
        mock_logger.error.assert_not_called()

    def test_performance_tracker_context_manager_success(self):
        """Test PerformanceTracker as context manager with success."""
        mock_logger = Mock()

        with PerformanceTracker("context_test", logger_instance=mock_logger) as tracker:
            time.sleep(0.01)
            assert tracker.start_time is not None

        # Should log both start and completion
        assert mock_logger.info.call_count >= 2

    def test_performance_tracker_context_manager_with_exception(self):
        """Test PerformanceTracker as context manager with exception."""
        mock_logger = Mock()

        with pytest.raises(ValueError):
            with PerformanceTracker("context_test", logger_instance=mock_logger):
                time.sleep(0.01)
                raise ValueError("Test exception")

        # Should log start and error
        mock_logger.info.assert_called()  # Start log
        mock_logger.error.assert_called_once()  # Error log

    def test_performance_tracker_duration_property_before_start(self):
        """Test duration_ms property before start."""
        tracker = PerformanceTracker("test_op")
        assert tracker.duration_ms is None

    def test_performance_tracker_duration_property_during_operation(self):
        """Test duration_ms property during operation."""
        tracker = PerformanceTracker("test_op")
        tracker.start()
        time.sleep(0.01)

        duration = tracker.duration_ms
        assert duration is not None
        assert duration >= 10

    def test_performance_tracker_duration_property_after_stop(self):
        """Test duration_ms property after stop."""
        tracker = PerformanceTracker("test_op")
        tracker.start()
        time.sleep(0.01)
        stop_duration = tracker.stop()

        # Property should return the same as stop()
        assert tracker.duration_ms == stop_duration


class TestLogFunctionCallDecorator:
    """Test log_function_call decorator functionality."""

    def test_log_function_call_sync_default_params(self):
        """Test decorator on sync function with default parameters."""
        with patch("backend.app.utils.logger.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @log_function_call()
            def test_function(x, y=10):
                return x + y

            result = test_function(5, y=15)

            assert result == 20
            # Should log start and completion
            mock_logger.info.assert_called()

    def test_log_function_call_sync_with_logging_options(self):
        """Test decorator with logging options enabled."""
        with patch("backend.app.utils.logger.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @log_function_call(
                operation_name="custom_sync_op", log_args=True, log_result=True
            )
            def test_function(x, y=10):
                return x * y

            result = test_function(3, y=7)

            assert result == 21
            # Should log arguments and result
            mock_logger.debug.assert_called()

    @pytest.mark.asyncio
    async def test_log_function_call_async_function(self):
        """Test decorator on async function."""
        with patch("backend.app.utils.logger.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @log_function_call(operation_name="async_test")
            async def async_function(value):
                await asyncio.sleep(0.01)
                return value * 2

            result = await async_function(5)

            assert result == 10
            # Should log operation
            mock_logger.info.assert_called()

    def test_log_function_call_sync_with_exception(self):
        """Test decorator handling exceptions in sync function."""
        with patch("backend.app.utils.logger.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @log_function_call(operation_name="failing_sync")
            def failing_function():
                raise ValueError("Sync function error")

            with pytest.raises(ValueError):
                failing_function()

            # Should still log the operation start
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_log_function_call_async_with_exception(self):
        """Test decorator handling exceptions in async function."""
        with patch("backend.app.utils.logger.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @log_function_call(operation_name="failing_async")
            async def failing_async_function():
                await asyncio.sleep(0.01)
                raise RuntimeError("Async function error")

            with pytest.raises(RuntimeError):
                await failing_async_function()

            # Should log operation
            mock_logger.info.assert_called()

    def test_log_function_call_min_duration_threshold(self):
        """Test decorator with minimum duration threshold."""
        with patch("backend.app.utils.logger.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @log_function_call(min_duration_ms=50.0)
            def fast_function():
                # Very fast function, should be below threshold
                return "fast"

            result = fast_function()

            assert result == "fast"
            # May not log completion due to threshold, but should log start
            mock_logger.info.assert_called()

    def test_log_function_call_preserves_function_metadata(self):
        """Test that decorator preserves original function metadata."""

        @log_function_call()
        def documented_function(param):
            """This is a test function."""
            return param

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."


class TestLogDictSafely:
    """Test log_dict_safely utility function."""

    def test_log_dict_safely_normal_values(self):
        """Test log_dict_safely with normal values."""
        data = {"string": "normal string", "number": 42, "boolean": True, "none": None}

        result = log_dict_safely(data)

        assert result == data  # Should be unchanged

    def test_log_dict_safely_long_strings(self):
        """Test log_dict_safely with long strings."""
        long_string = "x" * 1500
        data = {"long_value": long_string}

        result = log_dict_safely(data, max_length=1000)

        assert len(result["long_value"]) <= 1020  # 1000 + "... (truncated)"
        assert result["long_value"].endswith("... (truncated)")

    def test_log_dict_safely_binary_data(self):
        """Test log_dict_safely with binary data."""
        binary_data = b"\x89PNG\r\n\x1a\n"
        data = {"bytes_data": binary_data, "bytearray_data": bytearray(binary_data)}

        result = log_dict_safely(data)

        assert result["bytes_data"] == f"<binary data: {len(binary_data)} bytes>"
        assert result["bytearray_data"] == f"<binary data: {len(binary_data)} bytes>"

    def test_log_dict_safely_nested_dict(self):
        """Test log_dict_safely with nested dictionaries."""
        data = {
            "nested": {
                "long_string": "x" * 1500,
                "normal": "value",
                "binary": b"binary data",
            },
            "normal": "top level",
        }

        result = log_dict_safely(data, max_length=100)

        assert result["normal"] == "top level"
        assert result["nested"]["normal"] == "value"
        assert result["nested"]["long_string"].endswith("... (truncated)")
        assert "<binary data:" in result["nested"]["binary"]

    def test_log_dict_safely_recursive_nesting(self):
        """Test log_dict_safely with deeply nested structures."""
        data = {
            "level1": {
                "level2": {"level3": {"long_string": "x" * 500, "binary": b"test"}}
            }
        }

        result = log_dict_safely(data, max_length=100)

        assert result["level1"]["level2"]["level3"]["long_string"].endswith(
            "... (truncated)"
        )
        assert "<binary data:" in result["level1"]["level2"]["level3"]["binary"]

    def test_log_dict_safely_custom_max_length(self):
        """Test log_dict_safely with custom max_length."""
        data = {"short": "12345", "medium": "1234567890"}

        result = log_dict_safely(data, max_length=8)

        assert result["short"] == "12345"  # Below limit
        assert result["medium"] == "12345678... (truncated)"  # Above limit


class TestLogExceptionContext:
    """Test log_exception_context utility function."""

    def test_log_exception_context_basic(self):
        """Test basic exception context logging."""
        mock_logger = Mock()
        exception = ValueError("Test error message")

        log_exception_context(
            mock_logger,
            "file processing",
            exception,
            file_id="test-123",
            operation_type="pdf_parse",
        )

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        assert "Exception during file processing" in call_args[0][0]
        assert call_args[1]["operation"] == "file processing"
        assert call_args[1]["exception_type"] == "ValueError"
        assert call_args[1]["exception_message"] == "Test error message"
        assert call_args[1]["file_id"] == "test-123"
        assert call_args[1]["operation_type"] == "pdf_parse"

    def test_log_exception_context_different_exception_types(self):
        """Test exception context logging with different exception types."""
        mock_logger = Mock()

        test_cases = [
            (RuntimeError("Runtime issue"), "RuntimeError"),
            (
                OSError("File not found"),
                "OSError",
            ),  # IOError is aliased to OSError in Python 3+
            (KeyError("missing_key"), "KeyError"),
            (Exception("Generic error"), "Exception"),
        ]

        for exception, expected_type in test_cases:
            mock_logger.reset_mock()

            log_exception_context(mock_logger, "test operation", exception)

            call_args = mock_logger.error.call_args
            assert call_args[1]["exception_type"] == expected_type

    def test_log_exception_context_no_additional_context(self):
        """Test exception context logging without additional context."""
        mock_logger = Mock()
        exception = Exception("Simple error")

        log_exception_context(mock_logger, "simple operation", exception)

        call_args = mock_logger.error.call_args
        expected_keys = {"operation", "exception_type", "exception_message"}
        actual_keys = set(call_args[1].keys())

        assert expected_keys.issubset(actual_keys)


class TestFileOperationLogger:
    """Test FileOperationLogger class functionality."""

    def test_file_operation_logger_initialization_default(self):
        """Test FileOperationLogger with default logger."""
        with patch("backend.app.utils.logger.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            file_logger = FileOperationLogger()

            assert file_logger.logger is mock_logger

    def test_file_operation_logger_initialization_custom(self):
        """Test FileOperationLogger with custom logger."""
        custom_logger = Mock()
        file_logger = FileOperationLogger(base_logger=custom_logger)

        assert file_logger.logger is custom_logger

    def test_upload_started_logging(self):
        """Test upload_started method."""
        mock_logger = Mock()
        file_logger = FileOperationLogger(base_logger=mock_logger)

        file_logger.upload_started(
            "test.pdf",
            1048576,  # 1MB
            content_type="application/pdf",
            client_ip="192.168.1.1",
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        assert "File upload started" in call_args[0][0]
        assert call_args[1]["operation"] == "file_upload"
        assert call_args[1]["filename"] == "test.pdf"
        assert call_args[1]["file_size_bytes"] == 1048576
        assert call_args[1]["file_size_mb"] == 1.0
        assert call_args[1]["content_type"] == "application/pdf"
        assert call_args[1]["client_ip"] == "192.168.1.1"

    def test_upload_completed_logging(self):
        """Test upload_completed method."""
        mock_logger = Mock()
        file_logger = FileOperationLogger(base_logger=mock_logger)

        file_logger.upload_completed(
            "file-123",
            "test.pdf",
            1500.75,  # 1.5 seconds
            mime_type="application/pdf",
            file_size_mb=2.5,
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        assert "File upload completed" in call_args[0][0]
        assert call_args[1]["operation"] == "file_upload"
        assert call_args[1]["file_id"] == "file-123"
        assert call_args[1]["filename"] == "test.pdf"
        assert call_args[1]["duration_ms"] == 1500.75
        assert call_args[1]["success"] is True
        assert call_args[1]["mime_type"] == "application/pdf"

    def test_upload_failed_logging(self):
        """Test upload_failed method."""
        mock_logger = Mock()
        file_logger = FileOperationLogger(base_logger=mock_logger)

        file_logger.upload_failed(
            "failed.pdf", "File too large", 750.25, error_code=413, client_ip="10.0.0.1"
        )

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        assert "File upload failed" in call_args[0][0]
        assert call_args[1]["operation"] == "file_upload"
        assert call_args[1]["filename"] == "failed.pdf"
        assert call_args[1]["error"] == "File too large"
        assert call_args[1]["duration_ms"] == 750.25
        assert call_args[1]["success"] is False
        assert call_args[1]["error_code"] == 413

    def test_processing_started_logging(self):
        """Test processing_started method."""
        mock_logger = Mock()
        file_logger = FileOperationLogger(base_logger=mock_logger)

        file_logger.processing_started(
            "file-456", "pdf_extraction", processor="pypdf", page_count=10
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        assert "File processing started: pdf_extraction" in call_args[0][0]
        assert call_args[1]["operation"] == "file_processing"
        assert call_args[1]["operation_type"] == "pdf_extraction"
        assert call_args[1]["file_id"] == "file-456"
        assert call_args[1]["processor"] == "pypdf"
        assert call_args[1]["page_count"] == 10

    def test_processing_completed_logging(self):
        """Test processing_completed method."""
        mock_logger = Mock()
        file_logger = FileOperationLogger(base_logger=mock_logger)

        file_logger.processing_completed(
            "file-789",
            "metadata_extraction",
            2500.5,
            fields_extracted=15,
            confidence_score=0.95,
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        assert "File processing completed: metadata_extraction" in call_args[0][0]
        assert call_args[1]["operation"] == "file_processing"
        assert call_args[1]["operation_type"] == "metadata_extraction"
        assert call_args[1]["file_id"] == "file-789"
        assert call_args[1]["duration_ms"] == 2500.5
        assert call_args[1]["success"] is True
        assert call_args[1]["fields_extracted"] == 15
        assert call_args[1]["confidence_score"] == 0.95

    def test_processing_failed_logging(self):
        """Test processing_failed method."""
        mock_logger = Mock()
        file_logger = FileOperationLogger(base_logger=mock_logger)

        file_logger.processing_failed(
            "file-error",
            "ocr_processing",
            "OCR engine timeout",
            5000.0,
            error_code="TIMEOUT",
            attempted_pages=5,
        )

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        assert "File processing failed: ocr_processing" in call_args[0][0]
        assert call_args[1]["operation"] == "file_processing"
        assert call_args[1]["operation_type"] == "ocr_processing"
        assert call_args[1]["file_id"] == "file-error"
        assert call_args[1]["error"] == "OCR engine timeout"
        assert call_args[1]["duration_ms"] == 5000.0
        assert call_args[1]["success"] is False
        assert call_args[1]["error_code"] == "TIMEOUT"
        assert call_args[1]["attempted_pages"] == 5

    def test_access_logged_method(self):
        """Test access_logged method."""
        mock_logger = Mock()
        file_logger = FileOperationLogger(base_logger=mock_logger)

        file_logger.access_logged(
            "file-access", "download", user_id="user-123", ip_address="192.168.1.100"
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        assert "File accessed: download" in call_args[0][0]
        assert call_args[1]["operation"] == "file_access"
        assert call_args[1]["access_type"] == "download"
        assert call_args[1]["file_id"] == "file-access"
        assert call_args[1]["user_id"] == "user-123"
        assert call_args[1]["ip_address"] == "192.168.1.100"

    def test_deletion_logged_success(self):
        """Test deletion_logged method with success."""
        mock_logger = Mock()
        file_logger = FileOperationLogger(base_logger=mock_logger)

        file_logger.deletion_logged(
            "file-delete", success=True, filename="deleted.pdf", user_id="admin"
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        assert "File deleted successfully" in call_args[0][0]
        assert call_args[1]["operation"] == "file_deletion"
        assert call_args[1]["file_id"] == "file-delete"
        assert call_args[1]["success"] is True
        assert call_args[1]["filename"] == "deleted.pdf"
        assert call_args[1]["user_id"] == "admin"

    def test_deletion_logged_failure(self):
        """Test deletion_logged method with failure."""
        mock_logger = Mock()
        file_logger = FileOperationLogger(base_logger=mock_logger)

        file_logger.deletion_logged(
            "file-fail-delete", success=False, error="Permission denied", error_code=403
        )

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        assert "File deletion failed" in call_args[0][0]
        assert call_args[1]["operation"] == "file_deletion"
        assert call_args[1]["file_id"] == "file-fail-delete"
        assert call_args[1]["success"] is False
        assert call_args[1]["error"] == "Permission denied"
        assert call_args[1]["error_code"] == 403


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple utilities."""

    def test_performance_tracker_with_file_logger(self):
        """Test PerformanceTracker used with FileOperationLogger."""
        mock_logger = Mock()
        file_logger = FileOperationLogger(base_logger=mock_logger)

        with PerformanceTracker("file_upload", logger_instance=mock_logger):
            time.sleep(0.01)
            file_logger.upload_started("integration_test.pdf", 1024)

        # Both should have logged
        assert mock_logger.info.call_count >= 2

    def test_exception_logging_with_performance_tracking(self):
        """Test exception logging combined with performance tracking."""
        mock_logger = Mock()

        try:
            with PerformanceTracker("failing_operation", logger_instance=mock_logger):
                raise ValueError("Integration test error")
        except ValueError as e:
            log_exception_context(
                mock_logger, "integration test", e, test_context="value"
            )

        # Should have both performance error log and exception context log
        assert mock_logger.error.call_count >= 2

    def test_log_dict_safely_with_file_context(self):
        """Test log_dict_safely with file operation context."""
        file_context = {
            "file_id": "test-123",
            "filename": "x" * 200,  # Long filename
            "content": b"binary file content",
            "metadata": {
                "pages": 10,
                "size_bytes": 1048576,
                "description": "y" * 150,  # Long description
            },
        }

        safe_context = log_dict_safely(file_context, max_length=100)

        assert safe_context["file_id"] == "test-123"
        assert safe_context["filename"].endswith("... (truncated)")
        assert "<binary data:" in safe_context["content"]
        assert safe_context["metadata"]["pages"] == 10
        assert safe_context["metadata"]["description"].endswith("... (truncated)")

    @pytest.mark.asyncio
    async def test_async_function_decorator_with_file_logging(self):
        """Test async function decorator integrated with file logging."""
        mock_logger = Mock()
        file_logger = FileOperationLogger(base_logger=mock_logger)

        @log_function_call(operation_name="async_file_process")
        async def process_file_async(file_id: str):
            await asyncio.sleep(0.01)
            file_logger.processing_started(file_id, "async_processing")
            return f"processed_{file_id}"

        result = await process_file_async("async-test-123")

        assert result == "processed_async-test-123"
        # Should have logged function execution (start and completion)
        assert mock_logger.info.call_count >= 1
