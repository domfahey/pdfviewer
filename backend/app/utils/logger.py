"""
Logging utilities and helper functions for the PDF Viewer API.

This module provides convenient functions and classes for common
logging patterns used throughout the application.
"""

import functools
import time
from typing import Any, Optional

import structlog

from ..core.logging import get_logger


class PerformanceTracker:
    """
    Context manager and utility class for tracking operation performance.

    Can be used as a context manager or decorator to automatically
    log performance metrics for operations.
    """

    def __init__(
        self,
        operation_name: str,
        logger_instance: Optional[structlog.stdlib.BoundLogger] = None,
        log_start: bool = True,
        min_duration_ms: float = 0.0,
        **context: Any,
    ):
        """
        Initialize performance tracker.

        Args:
            operation_name: Name of the operation being tracked
            logger_instance: Logger to use (defaults to module logger)
            log_start: Whether to log when operation starts
            min_duration_ms: Only log if duration exceeds this threshold
            **context: Additional context to include in logs
        """
        self.operation_name = operation_name
        self.logger = logger_instance or get_logger(__name__)
        self.log_start = log_start
        self.min_duration_ms = min_duration_ms
        self.context = context
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self) -> "PerformanceTracker":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop(
            exception=exc_type is not None, error=str(exc_val) if exc_val else None
        )

    def start(self) -> None:
        """Start timing the operation."""
        self.start_time = time.perf_counter()
        if self.log_start:
            self.logger.info(
                f"Starting {self.operation_name}",
                operation=self.operation_name,
                **self.context,
            )

    def stop(self, exception: bool = False, error: Optional[str] = None) -> float:
        """
        Stop timing and log the results.

        Args:
            exception: Whether the operation ended with an exception
            error: Error message if applicable

        Returns:
            Duration in milliseconds
        """
        if self.start_time is None:
            raise RuntimeError(
                "PerformanceTracker.start() must be called before stop()"
            )

        self.end_time = time.perf_counter()
        duration_ms = (self.end_time - self.start_time) * 1000

        # Only log if duration meets threshold
        if duration_ms >= self.min_duration_ms:
            log_data = {
                "operation": self.operation_name,
                "duration_ms": round(duration_ms, 2),
                "success": not exception,
                **self.context,
            }

            if exception and error:
                log_data["error"] = error
                self.logger.error(f"Failed {self.operation_name}", **log_data)
            else:
                self.logger.info(f"Completed {self.operation_name}", **log_data)

        return duration_ms

    @property
    def duration_ms(self) -> Optional[float]:
        """Get current duration in milliseconds."""
        if self.start_time is None:
            return None
        end_time = self.end_time or time.perf_counter()
        return (end_time - self.start_time) * 1000


def log_function_call(
    operation_name: Optional[str] = None,
    log_args: bool = False,
    log_result: bool = False,
    min_duration_ms: float = 0.0,
):
    """
    Decorator to automatically log function calls with performance tracking.

    Args:
        operation_name: Custom operation name (defaults to function name)
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        min_duration_ms: Only log if duration exceeds threshold
    """

    def decorator(func):
        op_name = operation_name or f"{func.__module__}.{func.__name__}"
        func_logger = get_logger(func.__module__)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = {"function": func.__name__}
            if log_args:
                context["args"] = str(args)
                context["kwargs"] = kwargs

            with PerformanceTracker(
                op_name, func_logger, min_duration_ms=min_duration_ms, **context
            ) as tracker:
                try:
                    result = await func(*args, **kwargs)
                    if log_result:
                        func_logger.debug(f"{op_name} result", result=str(result))
                    return result
                except Exception as e:
                    tracker.context["error_type"] = type(e).__name__
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = {"function": func.__name__}
            if log_args:
                context["args"] = str(args)
                context["kwargs"] = kwargs

            with PerformanceTracker(
                op_name, func_logger, min_duration_ms=min_duration_ms, **context
            ) as tracker:
                try:
                    result = func(*args, **kwargs)
                    if log_result:
                        func_logger.debug(f"{op_name} result", result=str(result))
                    return result
                except Exception as e:
                    tracker.context["error_type"] = type(e).__name__
                    raise

        # Return appropriate wrapper
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_dict_safely(data: dict[str, Any], max_length: int = 1000) -> dict[str, Any]:
    """
    Safely convert a dictionary for logging by truncating long values.

    Args:
        data: Dictionary to process
        max_length: Maximum length for string values

    Returns:
        Dictionary safe for logging
    """
    safe_dict = {}
    for key, value in data.items():
        if isinstance(value, str) and len(value) > max_length:
            safe_dict[key] = value[:max_length] + "... (truncated)"
        elif isinstance(value, (bytes, bytearray)):
            safe_dict[key] = f"<binary data: {len(value)} bytes>"
        elif isinstance(value, dict):
            safe_dict[key] = log_dict_safely(value, max_length)  # type: ignore[assignment]
        else:
            safe_dict[key] = value
    return safe_dict


def log_exception_context(
    logger_instance: structlog.stdlib.BoundLogger,
    operation: str,
    exception: Exception,
    **context: Any,
) -> None:
    """
    Log an exception with rich context information.

    Args:
        logger_instance: Logger to use
        operation: Description of what was happening when exception occurred
        exception: The exception that was raised
        **context: Additional context to include
    """
    logger_instance.error(
        f"Exception during {operation}",
        operation=operation,
        exception_type=type(exception).__name__,
        exception_message=str(exception),
        **context,
    )


class FileOperationLogger:
    """
    Specialized logger for file operations with consistent context.

    Provides methods for logging common file operations like upload,
    download, processing, and deletion with standard context fields.
    """

    def __init__(self, base_logger: Optional[structlog.stdlib.BoundLogger] = None):
        self.logger = base_logger or get_logger(__name__)

    def upload_started(self, filename: str, file_size: int, **context: Any) -> None:
        """Log the start of a file upload."""
        self.logger.info(
            "File upload started",
            operation="file_upload",
            filename=filename,
            file_size_bytes=file_size,
            file_size_mb=round(file_size / (1024 * 1024), 2),
            **context,
        )

    def upload_completed(
        self, file_id: str, filename: str, duration_ms: float, **context: Any
    ) -> None:
        """Log successful file upload completion."""
        self.logger.info(
            "File upload completed",
            operation="file_upload",
            file_id=file_id,
            filename=filename,
            duration_ms=round(duration_ms, 2),
            success=True,
            **context,
        )

    def upload_failed(
        self, filename: str, error: str, duration_ms: float, **context: Any
    ) -> None:
        """Log failed file upload."""
        self.logger.error(
            "File upload failed",
            operation="file_upload",
            filename=filename,
            error=error,
            duration_ms=round(duration_ms, 2),
            success=False,
            **context,
        )

    def processing_started(
        self, file_id: str, operation_type: str, **context: Any
    ) -> None:
        """Log the start of file processing."""
        self.logger.info(
            f"File processing started: {operation_type}",
            operation="file_processing",
            operation_type=operation_type,
            file_id=file_id,
            **context,
        )

    def processing_completed(
        self, file_id: str, operation_type: str, duration_ms: float, **context: Any
    ) -> None:
        """Log successful file processing completion."""
        self.logger.info(
            f"File processing completed: {operation_type}",
            operation="file_processing",
            operation_type=operation_type,
            file_id=file_id,
            duration_ms=round(duration_ms, 2),
            success=True,
            **context,
        )

    def processing_failed(
        self,
        file_id: str,
        operation_type: str,
        error: str,
        duration_ms: float,
        **context: Any,
    ) -> None:
        """Log failed file processing."""
        self.logger.error(
            f"File processing failed: {operation_type}",
            operation="file_processing",
            operation_type=operation_type,
            file_id=file_id,
            error=error,
            duration_ms=round(duration_ms, 2),
            success=False,
            **context,
        )

    def access_logged(self, file_id: str, operation: str, **context: Any) -> None:
        """Log file access operations."""
        self.logger.info(
            f"File accessed: {operation}",
            operation="file_access",
            access_type=operation,
            file_id=file_id,
            **context,
        )

    def deletion_logged(self, file_id: str, success: bool, **context: Any) -> None:
        """Log file deletion operations."""
        if success:
            self.logger.info(
                "File deleted successfully",
                operation="file_deletion",
                file_id=file_id,
                success=True,
                **context,
            )
        else:
            self.logger.error(
                "File deletion failed",
                operation="file_deletion",
                file_id=file_id,
                success=False,
                **context,
            )
