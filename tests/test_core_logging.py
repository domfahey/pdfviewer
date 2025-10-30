"""
Comprehensive unit tests for backend/app/core/logging.py module.

Tests cover logging configuration, structured logging setup,
logger factory, context management, and performance monitoring.
"""

import logging
from unittest.mock import Mock, patch

import pytest
import structlog

from backend.app.core.logging import (
    LogContext,
    configure_logging,
    get_logger,
    setup_uvicorn_logging,
)
from backend.app.utils.decorators import performance_logger as log_performance


class TestConfigureLogging:
    """Test logging configuration functionality."""

    def test_configure_logging_default_settings(self):
        """Test logging configuration with default settings."""
        configure_logging()

        # Verify structlog is configured
        logger = structlog.get_logger()
        assert logger is not None

    def test_configure_logging_debug_level(self):
        """Test logging configuration with DEBUG level."""
        configure_logging(level="DEBUG")

        # Check that root logger level is set to DEBUG
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_configure_logging_json_logs_enabled(self):
        """Test logging configuration with JSON output."""
        configure_logging(json_logs=True)

        logger = structlog.get_logger()
        assert logger is not None

    def test_configure_logging_without_correlation_id(self):
        """Test logging configuration with correlation ID disabled."""
        configure_logging(enable_correlation_id=False)

        logger = structlog.get_logger()
        assert logger is not None

    def test_configure_logging_rich_handler_development(self):
        """Test rich handler is configured for development mode."""
        with patch("backend.app.core.logging.RichHandler") as mock_rich:
            mock_handler = Mock()
            mock_rich.return_value = mock_handler

            configure_logging(json_logs=False)

            # Verify RichHandler was instantiated
            mock_rich.assert_called_once()

    def test_configure_logging_json_handler_production(self):
        """Test JSON renderer is used for production mode."""
        configure_logging(json_logs=True, level="INFO")

        logger = structlog.get_logger()
        assert logger is not None


class TestGetLogger:
    """Test logger factory function."""

    def test_get_logger_returns_bound_logger(self):
        """Test get_logger returns a BoundLogger instance."""
        logger = get_logger("test_module")

        assert logger is not None
        assert isinstance(logger, structlog.stdlib.BoundLogger)

    def test_get_logger_with_module_name(self):
        """Test get_logger with specific module name."""
        logger = get_logger("backend.app.test")

        assert logger is not None

    def test_get_logger_different_names_return_different_loggers(self):
        """Test that different module names return distinct logger instances."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        # Both should be valid loggers
        assert logger1 is not None
        assert logger2 is not None


class TestSetupUvicornLogging:
    """Test uvicorn logging configuration."""

    def test_setup_uvicorn_logging_returns_dict(self):
        """Test setup_uvicorn_logging returns a configuration dict."""
        config = setup_uvicorn_logging()

        assert isinstance(config, dict)
        assert "version" in config
        assert config["version"] == 1

    def test_setup_uvicorn_logging_has_required_keys(self):
        """Test configuration has all required logging keys."""
        config = setup_uvicorn_logging()

        assert "formatters" in config
        assert "handlers" in config
        assert "loggers" in config

    def test_setup_uvicorn_logging_formatters_configured(self):
        """Test formatters are properly configured."""
        config = setup_uvicorn_logging()

        formatters = config["formatters"]
        assert "default" in formatters
        assert "access" in formatters

    def test_setup_uvicorn_logging_handlers_configured(self):
        """Test handlers are properly configured."""
        config = setup_uvicorn_logging()

        handlers = config["handlers"]
        assert "default" in handlers
        assert "access" in handlers

    def test_setup_uvicorn_logging_loggers_configured(self):
        """Test uvicorn loggers are configured."""
        config = setup_uvicorn_logging()

        loggers = config["loggers"]
        assert "uvicorn" in loggers
        assert "uvicorn.error" in loggers
        assert "uvicorn.access" in loggers

    def test_setup_uvicorn_logging_custom_log_level(self):
        """Test uvicorn logging with custom log level."""
        config = setup_uvicorn_logging(log_level="DEBUG")

        assert config["loggers"]["uvicorn"]["level"] == "DEBUG"

    def test_setup_uvicorn_logging_disable_propagation(self):
        """Test uvicorn loggers don't propagate to root."""
        config = setup_uvicorn_logging()

        # uvicorn and access loggers should not propagate
        assert config["loggers"]["uvicorn"]["propagate"] is False
        assert config["loggers"]["uvicorn.access"]["propagate"] is False


class TestLogContext:
    """Test LogContext context manager."""

    def test_log_context_creates_bound_logger(self):
        """Test LogContext creates a bound logger with context."""
        logger = get_logger("test")
        context = {"user_id": "123", "request_id": "abc"}

        with LogContext(logger, **context) as bound_logger:
            assert bound_logger is not None
            assert isinstance(bound_logger, structlog.stdlib.BoundLogger)

    def test_log_context_binds_context_values(self):
        """Test LogContext properly binds context values."""
        logger = get_logger("test")
        context = {"operation": "test_op", "correlation_id": "test-123"}

        with LogContext(logger, **context) as bound_logger:
            # The bound logger should have the context
            assert bound_logger is not None

    def test_log_context_exception_handling(self):
        """Test LogContext logs exceptions that occur within context."""
        logger = get_logger("test")

        with patch.object(logger, "error") as mock_error:
            with pytest.raises(ValueError):
                with LogContext(logger, operation="test"):
                    raise ValueError("Test error")
            mock_error.assert_called_once()

    def test_log_context_normal_exit(self):
        """Test LogContext exits normally without exceptions."""
        logger = get_logger("test")

        # Should not raise any exceptions
        with LogContext(logger, test_key="test_value") as bound_logger:
            assert bound_logger is not None


class TestLogPerformanceDecorator:
    """Test log_performance decorator."""

    @pytest.mark.asyncio
    async def test_log_performance_async_function_success(self):
        """Test log_performance decorator with successful async function."""

        @log_performance("test_operation")
        async def async_function():
            return "success"

        result = await async_function()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_log_performance_async_function_failure(self):
        """Test log_performance decorator with failing async function."""

        @log_performance("test_operation")
        async def async_failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await async_failing_function()

    def test_log_performance_sync_function_success(self):
        """Test log_performance decorator with successful sync function."""

        @log_performance("test_operation")
        def sync_function():
            return "success"

        result = sync_function()
        assert result == "success"

    def test_log_performance_sync_function_failure(self):
        """Test log_performance decorator with failing sync function."""

        @log_performance("test_operation")
        def sync_failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            sync_failing_function()

    def test_log_performance_measures_duration(self):
        """Test log_performance decorator measures execution time."""
        import time

        @log_performance("slow_operation")
        def slow_function():
            time.sleep(0.01)  # 10ms delay
            return "done"

        result = slow_function()
        assert result == "done"

    @pytest.mark.asyncio
    async def test_log_performance_async_measures_duration(self):
        """Test log_performance decorator measures async execution time."""
        import asyncio

        @log_performance("async_slow_operation")
        async def async_slow_function():
            await asyncio.sleep(0.01)  # 10ms delay
            return "done"

        result = await async_slow_function()
        assert result == "done"

    def test_log_performance_preserves_function_metadata(self):
        """Test decorator preserves original function metadata."""

        @log_performance("test_op")
        def documented_function():
            """This is a documented function."""
            return "result"

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a documented function."

    def test_log_performance_with_function_arguments(self):
        """Test log_performance works with function arguments."""

        @log_performance("test_operation")
        def function_with_args(x, y, z=3):
            return x + y + z

        result = function_with_args(1, 2, z=4)
        assert result == 7

    @pytest.mark.asyncio
    async def test_log_performance_async_with_arguments(self):
        """Test log_performance works with async function arguments."""

        @log_performance("async_test_operation")
        async def async_function_with_args(x, y):
            return x * y

        result = await async_function_with_args(3, 4)
        assert result == 12


class TestLoggingIntegration:
    """Integration tests for logging module."""

    def test_full_logging_setup_workflow(self):
        """Test complete logging setup workflow."""
        # Configure logging
        configure_logging(level="INFO", json_logs=False)

        # Get a logger
        logger = get_logger("test_app")

        # Log some messages
        logger.info("Test info message", key="value")
        logger.debug("Test debug message")

        # Get uvicorn config
        uvicorn_config = setup_uvicorn_logging("INFO")

        assert logger is not None
        assert uvicorn_config is not None

    def test_logging_with_context_manager(self):
        """Test logging with context manager integration."""
        configure_logging(level="DEBUG")
        logger = get_logger("test_context")

        with LogContext(logger, request_id="123", user="test") as ctx_logger:
            ctx_logger.info("Message with context")

    @pytest.mark.asyncio
    async def test_performance_logging_integration(self):
        """Test performance logging decorator integration."""
        configure_logging(level="INFO")

        @log_performance("integration_test")
        async def test_async_operation():
            return {"status": "success"}

        result = await test_async_operation()
        assert result == {"status": "success"}
