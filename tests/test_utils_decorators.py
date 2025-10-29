"""Unit tests for backend/app/utils/decorators.py module.

Tests cover the unified async/sync wrapper factory and performance
logging decorator that consolidates duplicated code.
"""

import asyncio
import time
from unittest.mock import MagicMock, Mock, patch

import pytest
import structlog

from backend.app.utils.decorators import (
    create_async_sync_wrapper,
    performance_logger,
)


class TestCreateAsyncSyncWrapper:
    """Test the unified async/sync wrapper factory."""

    def test_sync_function_wrapper(self):
        """Test wrapping a synchronous function."""
        before_called = []
        after_called = []

        def before(args, kwargs):
            before_called.append((args, kwargs))

        def after(result, duration):
            after_called.append((result, duration))

        @create_async_sync_wrapper
        def sync_func(x, y):
            return x + y

        wrapped = create_async_sync_wrapper(
            sync_func,
            before_call=before,
            after_call=after,
        )

        result = wrapped(2, 3)

        assert result == 5
        assert len(before_called) == 1
        assert len(after_called) == 1
        assert after_called[0][0] == 5  # result
        assert after_called[0][1] > 0  # duration

    @pytest.mark.asyncio
    async def test_async_function_wrapper(self):
        """Test wrapping an asynchronous function."""
        before_called = []
        after_called = []

        def before(args, kwargs):
            before_called.append((args, kwargs))

        def after(result, duration):
            after_called.append((result, duration))

        async def async_func(x, y):
            await asyncio.sleep(0.01)
            return x + y

        wrapped = create_async_sync_wrapper(
            async_func,
            before_call=before,
            after_call=after,
        )

        result = await wrapped(2, 3)

        assert result == 5
        assert len(before_called) == 1
        assert len(after_called) == 1
        assert after_called[0][0] == 5  # result
        assert after_called[0][1] >= 0.01  # duration should be at least 10ms

    def test_sync_function_with_error(self):
        """Test error handling in sync wrapper."""
        error_called = []

        def on_error(exc, duration):
            error_called.append((exc, duration))

        def failing_func():
            raise ValueError("test error")

        wrapped = create_async_sync_wrapper(
            failing_func,
            on_error=on_error,
        )

        with pytest.raises(ValueError, match="test error"):
            wrapped()

        assert len(error_called) == 1
        assert isinstance(error_called[0][0], ValueError)
        assert error_called[0][1] > 0  # duration

    @pytest.mark.asyncio
    async def test_async_function_with_error(self):
        """Test error handling in async wrapper."""
        error_called = []

        def on_error(exc, duration):
            error_called.append((exc, duration))

        async def failing_func():
            await asyncio.sleep(0.01)
            raise ValueError("test error")

        wrapped = create_async_sync_wrapper(
            failing_func,
            on_error=on_error,
        )

        with pytest.raises(ValueError, match="test error"):
            await wrapped()

        assert len(error_called) == 1
        assert isinstance(error_called[0][0], ValueError)
        assert error_called[0][1] >= 0.01  # duration

    def test_wrapper_without_callbacks(self):
        """Test wrapper works without any callbacks."""

        def simple_func(x):
            return x * 2

        wrapped = create_async_sync_wrapper(simple_func)

        result = wrapped(5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_async_wrapper_without_callbacks(self):
        """Test async wrapper works without any callbacks."""

        async def simple_async_func(x):
            await asyncio.sleep(0.001)
            return x * 2

        wrapped = create_async_sync_wrapper(simple_async_func)

        result = await wrapped(5)
        assert result == 10


class TestPerformanceLogger:
    """Test the unified performance logging decorator."""

    @patch("backend.app.utils.decorators.structlog.get_logger")
    def test_sync_function_logging(self, mock_get_logger):
        """Test performance logging for sync functions."""
        mock_logger = MagicMock()
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger
        mock_get_logger.return_value = mock_logger

        @performance_logger("test_operation")
        def sync_func(x):
            return x * 2

        result = sync_func(5)

        assert result == 10

        # Verify logger was called
        assert mock_logger.bind.called
        assert mock_bound_logger.info.called

        # Check that operation start was logged
        info_calls = mock_bound_logger.info.call_args_list
        assert len(info_calls) == 2  # start and complete

        # Verify start message
        start_call = info_calls[0]
        assert "Starting test_operation" in start_call[0]

        # Verify completion message
        complete_call = info_calls[1]
        assert "Completed test_operation" in complete_call[0]

    @pytest.mark.asyncio
    @patch("backend.app.utils.decorators.structlog.get_logger")
    async def test_async_function_logging(self, mock_get_logger):
        """Test performance logging for async functions."""
        mock_logger = MagicMock()
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger
        mock_get_logger.return_value = mock_logger

        @performance_logger("async_operation")
        async def async_func(x):
            await asyncio.sleep(0.01)
            return x * 2

        result = await async_func(5)

        assert result == 10
        assert mock_logger.bind.called
        assert mock_bound_logger.info.called

    @patch("backend.app.utils.decorators.structlog.get_logger")
    def test_error_logging(self, mock_get_logger):
        """Test error logging in performance decorator."""
        mock_logger = MagicMock()
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger
        mock_get_logger.return_value = mock_logger

        @performance_logger("failing_operation")
        def failing_func():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            failing_func()

        # Verify error was logged
        assert mock_bound_logger.error.called
        error_call = mock_bound_logger.error.call_args_list[0]
        assert "Failed failing_operation" in error_call[0]

    @patch("backend.app.utils.decorators.structlog.get_logger")
    def test_log_args_enabled(self, mock_get_logger):
        """Test logging with arguments enabled."""
        mock_logger = MagicMock()
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger
        mock_get_logger.return_value = mock_logger

        @performance_logger("operation_with_args", log_args=True)
        def func_with_args(x, y, z=10):
            return x + y + z

        result = func_with_args(1, 2, z=3)

        assert result == 6

        # Check that args were logged in the bind call
        bind_call = mock_logger.bind.call_args_list[0]
        context = bind_call[1]
        assert "args" in context or "kwargs" in context

    @patch("backend.app.utils.decorators.structlog.get_logger")
    def test_min_duration_threshold(self, mock_get_logger):
        """Test minimum duration threshold filtering."""
        mock_logger = MagicMock()
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger
        mock_get_logger.return_value = mock_logger

        # Set very high threshold
        @performance_logger("fast_operation", min_duration_ms=10000.0)
        def fast_func():
            return "done"

        result = fast_func()

        assert result == "done"

        # Start should be logged, but complete should be filtered out
        # due to not meeting threshold
        info_calls = mock_bound_logger.info.call_args_list
        # Only the start call should be made
        assert len(info_calls) == 1
        assert "Starting" in info_calls[0][0]

    @patch("backend.app.utils.decorators.structlog.get_logger")
    def test_custom_logger(self, mock_get_logger):
        """Test using a custom logger instance."""
        custom_logger = MagicMock()
        custom_bound_logger = MagicMock()
        custom_logger.bind.return_value = custom_bound_logger

        @performance_logger("custom_logger_op", logger=custom_logger)
        def func():
            return "done"

        result = func()

        assert result == "done"
        # Should use the custom logger, not call get_logger
        assert custom_logger.bind.called
        assert custom_bound_logger.info.called
