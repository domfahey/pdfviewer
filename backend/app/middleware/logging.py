"""
Logging middleware for request correlation and structured logging context.

This module provides middleware to add correlation IDs to requests and
enhance logging with request context throughout the application lifecycle.
"""

import time
import uuid
from contextvars import ContextVar
from typing import Callable, Optional

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to store correlation ID across async calls
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation IDs and log HTTP requests/responses.

    This middleware:
    1. Generates or extracts correlation IDs from headers
    2. Logs incoming requests with context
    3. Measures request duration
    4. Logs responses with status and timing
    5. Handles exceptions with proper logging
    """

    def __init__(self, app, correlation_header: str = "X-Correlation-ID"):
        super().__init__(app)
        self.correlation_header = correlation_header

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract correlation ID
        correlation_id = request.headers.get(self.correlation_header) or str(
            uuid.uuid4()
        )
        correlation_id_var.set(correlation_id)

        # Start timing the request
        start_time = time.perf_counter()

        # Extract request details for logging
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "user_agent": request.headers.get("user-agent"),
            "remote_addr": self._get_client_ip(request),
            "correlation_id": correlation_id,
        }

        # Log incoming request
        request_logger = logger.bind(**request_info)
        request_logger.info("Request started")

        try:
            # Process the request
            response = await call_next(request)

            # Calculate request duration
            duration = time.perf_counter() - start_time

            # Log successful response
            response_info = {
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "response_size": response.headers.get("content-length"),
            }

            request_logger.bind(**response_info).info("Request completed")

            # Add correlation ID to response headers
            response.headers[self.correlation_header] = correlation_id

            return response

        except Exception as exc:
            # Calculate request duration even for errors
            duration = time.perf_counter() - start_time

            # Log the exception
            request_logger.bind(
                duration_ms=round(duration * 1000, 2),
                error_type=type(exc).__name__,
                error_message=str(exc),
            ).error("Request failed with exception")

            # Re-raise the exception to be handled by FastAPI
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract the real client IP address from request headers."""
        # Check for forwarded headers (behind proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct connection IP
        return request.client.host if request.client else "unknown"


def add_correlation_id(logger, method_name, event_dict):
    """
    Structlog processor to add correlation ID to all log entries.

    This processor automatically adds the current correlation ID
    to every log entry when available.
    """
    correlation_id = correlation_id_var.get()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID from context."""
    return correlation_id_var.get()


def log_with_correlation(
    logger_instance: structlog.stdlib.BoundLogger, **extra_context
):
    """
    Create a logger bound with correlation ID and extra context.

    Args:
        logger_instance: The base logger instance
        **extra_context: Additional context to bind to the logger

    Returns:
        Logger bound with correlation ID and extra context
    """
    context = {"correlation_id": get_correlation_id()}
    context.update(extra_context)
    return logger_instance.bind(**context)


class RequestContextLogger:
    """
    Context manager to automatically add request context to logs.

    Usage:
        with RequestContextLogger(logger, request) as log:
            log.info("Processing file upload")
    """

    def __init__(self, logger_instance: structlog.stdlib.BoundLogger, request: Request):
        self.logger = logger_instance
        self.request = request
        self.context_logger: Optional[structlog.stdlib.BoundLogger] = None

    def __enter__(self) -> structlog.stdlib.BoundLogger:
        context = {
            "method": self.request.method,
            "path": self.request.url.path,
            "correlation_id": get_correlation_id(),
            "user_agent": self.request.headers.get("user-agent", "unknown"),
        }
        self.context_logger = self.logger.bind(**context)
        return self.context_logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and self.context_logger:
            self.context_logger.error(
                "Exception in request context",
                exc_type=exc_type.__name__,
                exc_value=str(exc_val),
            )


def log_file_operation(operation: str, filename: str, file_id: Optional[str] = None):
    """
    Decorator to log file operations with consistent context.

    Args:
        operation: Description of the file operation
        filename: Name of the file being operated on
        file_id: Optional file ID for tracking
    """

    def decorator(func):
        import asyncio
        import functools

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            operation_logger = log_with_correlation(
                logger,
                operation=operation,
                filename=filename,
                file_id=file_id,
            )

            start_time = time.perf_counter()
            operation_logger.info(f"Starting {operation}")

            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                operation_logger.info(
                    f"Completed {operation}",
                    duration_ms=round(duration * 1000, 2),
                    success=True,
                )
                return result
            except Exception as e:
                duration = time.perf_counter() - start_time
                operation_logger.error(
                    f"Failed {operation}",
                    duration_ms=round(duration * 1000, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                    success=False,
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            operation_logger = log_with_correlation(
                logger,
                operation=operation,
                filename=filename,
                file_id=file_id,
            )

            start_time = time.perf_counter()
            operation_logger.info(f"Starting {operation}")

            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                operation_logger.info(
                    f"Completed {operation}",
                    duration_ms=round(duration * 1000, 2),
                    success=True,
                )
                return result
            except Exception as e:
                duration = time.perf_counter() - start_time
                operation_logger.error(
                    f"Failed {operation}",
                    duration_ms=round(duration * 1000, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                    success=False,
                )
                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
