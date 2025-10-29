"""API logging decorators and utilities for enhanced request/response logging.

This module provides decorators and utilities for detailed API endpoint logging,
including parameter validation, response logging, and performance metrics.
"""

import functools
import time
from collections.abc import Callable
from typing import Any

import structlog
from fastapi import Request

from ..middleware.logging import get_correlation_id

logger = structlog.get_logger(__name__)


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_api_call(
    operation: str,
    log_params: bool = True,
    log_response: bool = False,
    log_timing: bool = True,
    sensitive_params: list[str] | None = None,
):
    """Provide detailed logging for API endpoint calls.

    Args:
        operation: Name of the operation being performed.
        log_params: Whether to log function parameters.
        log_response: Whether to log response data.
        log_timing: Whether to log execution timing.
        sensitive_params: List of parameter names to redact from logs.

    Returns:
        Callable: Decorated function with API logging.

    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Start timing
            start_time = time.perf_counter()

            # Extract request info if available
            request_info = {}
            for arg in args:
                if isinstance(arg, Request):
                    request_info = {
                        "method": arg.method,
                        "path": arg.url.path,
                        "remote_addr": arg.client.host if arg.client else "unknown",
                    }
                    break

            # Prepare logging context
            log_context = {
                "operation": operation,
                "correlation_id": get_correlation_id(),
                **request_info,
            }

            # Log parameters if requested
            if log_params:
                sanitized_kwargs = _sanitize_params(kwargs, sensitive_params or [])
                log_context["parameters"] = sanitized_kwargs

            # Log operation start
            bound_logger = logger.bind(**log_context)
            bound_logger.info(f"API operation started: {operation}")

            try:
                # Execute the function
                result = await func(*args, **kwargs)

                # Calculate timing
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

                # Prepare success context
                success_context = {"duration_ms": duration_ms, "status": "success"}

                # Log response if requested
                if log_response and result is not None:
                    success_context["response_type"] = type(result).__name__
                    if hasattr(result, "model_dump"):
                        # Pydantic model
                        success_context["response_data"] = _sanitize_response(
                            result.model_dump()
                        )
                    elif isinstance(result, dict):
                        success_context["response_data"] = _sanitize_response(result)

                bound_logger.bind(**success_context).info(
                    f"API operation completed: {operation}"
                )

                return result

            except Exception as exc:
                # Calculate timing for errors
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

                # Log error
                error_context = {
                    "duration_ms": duration_ms,
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }

                bound_logger.bind(**error_context).error(
                    f"API operation failed: {operation}"
                )

                # Re-raise the exception
                raise

        return wrapper

    return decorator


def log_file_operation(
    operation: str,
    file_param: str = "file",
    log_file_details: bool = True,
):
    """Log file operations with consistent context and details.

    Args:
        operation: Name of the file operation.
        file_param: Name of the file parameter in function kwargs.
        log_file_details: Whether to log file details (name, size, type).

    Returns:
        Callable: Decorated function with file operation logging.

    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            # Extract file information
            file_info = {}
            if file_param in kwargs and log_file_details:
                file_obj = kwargs[file_param]
                if hasattr(file_obj, "filename"):
                    file_info = {
                        "filename": file_obj.filename,
                        "content_type": getattr(file_obj, "content_type", "unknown"),
                        "size": getattr(file_obj, "size", "unknown"),
                    }

            # Prepare logging context
            log_context = {
                "operation": operation,
                "correlation_id": get_correlation_id(),
                **file_info,
            }

            bound_logger = logger.bind(**log_context)
            bound_logger.info(f"File operation started: {operation}")

            try:
                result = await func(*args, **kwargs)

                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

                success_context = {
                    "duration_ms": duration_ms,
                    "status": "success",
                }

                # Add result info if it's a file operation response
                if hasattr(result, "file_id"):
                    success_context["file_id"] = result.file_id

                bound_logger.bind(**success_context).info(
                    f"File operation completed: {operation}"
                )

                return result

            except Exception as exc:
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

                error_context = {
                    "duration_ms": duration_ms,
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }

                bound_logger.bind(**error_context).error(
                    f"File operation failed: {operation}"
                )
                raise

        return wrapper

    return decorator


def _sanitize_params(
    params: dict[str, Any], sensitive_keys: list[str]
) -> dict[str, Any]:
    """Sanitize parameters for logging by redacting sensitive information.

    Args:
        params: Dictionary of parameters to sanitize
        sensitive_keys: List of keys to redact

    Returns:
        Sanitized parameters dictionary

    """
    sanitized = {}
    for key, value in params.items():
        if key.lower() in [k.lower() for k in sensitive_keys]:
            sanitized[key] = "[REDACTED]"
        elif hasattr(value, "__dict__") and not isinstance(
            value, str | int | float | bool
        ):
            # For complex objects, just log the type
            sanitized[key] = f"<{type(value).__name__}>"
        else:
            sanitized[key] = value
    return sanitized


def _sanitize_response(response_data: dict[str, Any]) -> dict[str, Any]:
    """Sanitize response data for logging.

    Args:
        response_data: Response data to sanitize

    Returns:
        Sanitized response data

    """
    # Define sensitive fields that should be redacted
    sensitive_fields = ["password", "token", "secret", "key", "auth"]

    sanitized: dict[str, Any] = {}
    for key, value in response_data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_response(value)
        else:
            sanitized[key] = value

    return sanitized


class APILogger:
    """Specialized logger for API operations with context binding."""

    def __init__(self, operation: str, correlation_id: str | None = None):
        """Initialize API logger with operation context.

        Args:
            operation: Name of the API operation
            correlation_id: Optional correlation ID (auto-detected if not provided)

        """
        self.operation = operation
        self.operation_name = operation  # For test compatibility
        self.correlation_id = correlation_id or get_correlation_id()
        self.start_time = time.perf_counter()
        self.context: dict[str, Any] = {}
        self.logger = get_logger(__name__).bind(
            operation=operation,
            correlation_id=self.correlation_id,
        )

    def log_request_received(self, **context):
        """Log that a request has been received."""
        self.logger.bind(**context).info(f"Request received for {self.operation}")

    def log_validation_start(self, **context):
        """Log start of validation process."""
        self.logger.bind(**context).info(f"Validation started for {self.operation}")

    def log_validation_success(self, **context):
        """Log successful validation."""
        self.logger.bind(**context).info(f"Validation passed for {self.operation}")

    def log_validation_error(self, error: str, **context):
        """Log validation error."""
        self.logger.bind(error=error, **context).error(
            f"Validation failed for {self.operation}"
        )

    def log_processing_start(self, **context):
        """Log start of main processing."""
        self.logger.bind(**context).info(f"Processing started for {self.operation}")

    def log_processing_success(self, **context):
        """Log successful processing."""
        self.logger.bind(**context).info(f"Processing completed for {self.operation}")

    def log_processing_error(self, error: Exception, **context):
        """Log processing error."""
        self.logger.bind(
            error_type=type(error).__name__, error_message=str(error), **context
        ).error(f"Processing failed for {self.operation}")

    def log_response_prepared(self, **context):
        """Log that response has been prepared."""
        self.logger.bind(**context).info(f"Response prepared for {self.operation}")

    def log_api_completed(
        self, status_code: int = 200, response_size: int = 0, **context
    ):
        """Log that API operation has completed."""
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        self.logger.bind(
            status_code=status_code,
            response_size=response_size,
            duration_ms=duration_ms,
            **context,
        ).info(f"API operation completed for {self.operation}")

    def log_file_received(
        self, filename: str | None = None, file_size: int = 0, **context
    ):
        """Log that a file has been received."""
        self.logger.bind(filename=filename, file_size=file_size, **context).info(
            f"File received for {self.operation}"
        )

    def log_file_processed(self, filename: str | None = None, **context):
        """Log that a file has been processed."""
        self.logger.bind(filename=filename, **context).info(
            f"File processed for {self.operation}"
        )
