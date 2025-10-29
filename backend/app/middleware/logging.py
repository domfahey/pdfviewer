"""Logging middleware for request correlation and structured logging context.

This module provides middleware to add correlation IDs to requests and
enhance logging with request context throughout the application lifecycle.
"""

import json
import os
import time
import uuid
from contextvars import ContextVar

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to store correlation ID across async calls
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for comprehensive request/response logging.

    This middleware:
    1. Generates or extracts correlation IDs from headers
    2. Logs incoming requests with context and optional body
    3. Measures request duration
    4. Logs responses with status, timing, and optional body
    5. Handles exceptions with proper logging
    6. Configurable request/response body logging for debugging
    """

    def __init__(
        self,
        app,
        correlation_header: str = "X-Correlation-ID",
        log_request_bodies: bool | None = None,
        log_response_bodies: bool | None = None,
        max_body_size: int = 4096,  # 4KB default limit
    ):  # type: ignore[misc]
        """Initialize the logging middleware.

        Args:
            app: The FastAPI application instance.
            correlation_header: Header name for correlation ID tracking. Defaults to "X-Correlation-ID".
            log_request_bodies: Whether to log request bodies. If None, uses LOG_REQUEST_BODIES env var.
            log_response_bodies: Whether to log response bodies. If None, uses LOG_RESPONSE_BODIES env var.
            max_body_size: Maximum size of request/response body to log in bytes. Defaults to 4KB.

        """
        super().__init__(app)
        self.correlation_header = correlation_header

        # Use environment variables with defaults - disabled by default for performance
        self.log_request_bodies = (
            log_request_bodies
            if log_request_bodies is not None
            else (
                os.getenv("LOG_REQUEST_BODIES", "false").lower()
                == "true"  # Changed default to false
            )
        )
        self.log_response_bodies = (
            log_response_bodies
            if log_response_bodies is not None
            else (
                os.getenv("LOG_RESPONSE_BODIES", "false").lower()
                == "true"  # Changed default to false
            )
        )
        self.max_body_size = int(os.getenv("MAX_BODY_LOG_SIZE", str(max_body_size)))

        # Define sensitive headers to filter
        self.sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "authentication",
            "proxy-authorization",
        }

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[misc]
        """Process HTTP request through the logging middleware.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler in the chain.

        Returns:
            Response: The HTTP response with correlation ID header added.

        """
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
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length"),
        }

        # Add filtered headers for debugging
        if os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG":
            request_info["headers"] = self._filter_headers(dict(request.headers))

        # Log request body if enabled and size is reasonable
        request_body = None
        if self.log_request_bodies and self._should_log_body(request):
            request_body = await self._safe_read_body(request)
            if request_body:
                request_info["request_body"] = self._sanitize_body(
                    request_body, request.headers.get("content-type")
                )

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
                "response_content_type": response.headers.get("content-type"),
            }

            # Add response headers for debugging
            if os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG":
                response_info["response_headers"] = self._filter_headers(
                    dict(response.headers)
                )

            # Log response body if enabled and appropriate
            if self.log_response_bodies and self._should_log_response_body(response):
                response_body = await self._safe_read_response_body(response)
                if response_body:
                    response_info["response_body"] = self._sanitize_body(
                        response_body, response.headers.get("content-type")
                    )

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

    def _filter_headers(self, headers: dict) -> dict:
        """Filter sensitive headers for logging."""
        filtered = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                filtered[key] = "[REDACTED]"
            else:
                filtered[key] = value
        return filtered

    def _should_log_body(self, request: Request) -> bool:
        """Determine if request body should be logged."""
        content_type = request.headers.get("content-type", "")
        content_length = request.headers.get("content-length")

        # Don't log large files
        if content_length and int(content_length) > self.max_body_size:
            return False

        # Don't log binary content
        if any(
            binary_type in content_type.lower()
            for binary_type in [
                "image/",
                "video/",
                "audio/",
                "application/pdf",
                "application/octet-stream",
            ]
        ):
            return False

        return True

    def _should_log_response_body(self, response: Response) -> bool:
        """Determine if response body should be logged."""
        content_type = response.headers.get("content-type", "")
        content_length = response.headers.get("content-length")

        # Don't log large responses
        if content_length and int(content_length) > self.max_body_size:
            return False

        # Don't log binary content or file downloads
        if any(
            binary_type in content_type.lower()
            for binary_type in [
                "image/",
                "video/",
                "audio/",
                "application/pdf",
                "application/octet-stream",
            ]
        ):
            return False

        return True

    async def _safe_read_body(self, request: Request) -> str | None:
        """Safely read request body with size limits."""
        try:
            body = await request.body()
            if len(body) > self.max_body_size:
                return f"[BODY TOO LARGE: {len(body)} bytes]"

            # Try to decode as text
            try:
                return body.decode("utf-8")
            except UnicodeDecodeError:
                return f"[BINARY CONTENT: {len(body)} bytes]"

        except Exception as read_error:
            return f"[ERROR READING BODY: {str(read_error)}]"

    async def _safe_read_response_body(self, response: Response) -> str | None:
        """Safely read response body with size limits."""
        try:
            # For StreamingResponse or FileResponse, we can't read the body
            if hasattr(response, "body_iterator") or hasattr(response, "path"):
                return "[STREAMING/FILE RESPONSE]"

            if hasattr(response, "body"):
                body = response.body
                if isinstance(body, bytes):
                    if len(body) > self.max_body_size:
                        return f"[BODY TOO LARGE: {len(body)} bytes]"

                    try:
                        return body.decode("utf-8")
                    except UnicodeDecodeError:
                        return f"[BINARY CONTENT: {len(body)} bytes]"

        except Exception as response_error:
            return f"[ERROR READING RESPONSE: {str(response_error)}]"

        return None

    def _sanitize_body(self, body: str, content_type: str | None) -> str:
        """Sanitize body content for logging."""
        if not body:
            return body

        # Handle JSON content
        if content_type and "application/json" in content_type:
            try:
                data = json.loads(body)
                return json.dumps(self._sanitize_json_data(data), indent=2)
            except json.JSONDecodeError:
                pass

        # For other content types, truncate if too long
        if len(body) > self.max_body_size:
            return body[: self.max_body_size] + "...[TRUNCATED]"

        return body

    def _sanitize_json_data(self, data):
        """Recursively sanitize JSON data."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if any(
                    sensitive in key.lower()
                    for sensitive in ["password", "token", "secret", "key", "auth"]
                ):
                    sanitized[key] = "[REDACTED]"
                else:
                    sanitized[key] = self._sanitize_json_data(value)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_json_data(item) for item in data]
        else:
            return data


def add_correlation_id(logger, method_name, event_dict):
    """Structlog processor to add correlation ID to all log entries.

    This processor automatically adds the current correlation ID
    to every log entry when available.
    """
    correlation_id = correlation_id_var.get()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def get_correlation_id() -> str | None:
    """Get the current correlation ID from context."""
    correlation_id = correlation_id_var.get()
    if correlation_id is None:
        # Generate a new correlation ID if none exists
        import uuid

        correlation_id = str(uuid.uuid4())
        correlation_id_var.set(correlation_id)
    return correlation_id


def set_correlation_id(correlation_id: str | None) -> None:
    """Set the correlation ID in the current context."""
    correlation_id_var.set(correlation_id)


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_with_correlation(
    logger_instance: structlog.stdlib.BoundLogger, **extra_context
):
    """Create a logger bound with correlation ID and extra context.

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
    """Context manager to automatically add request context to logs.

    Usage:
        with RequestContextLogger(logger, request) as log:
            log.info("Processing file upload")
    """

    def __init__(self, logger_instance: structlog.stdlib.BoundLogger, request: Request):
        """Initialize the request context logger.

        Args:
            logger_instance: The base logger instance to bind context to.
            request: The HTTP request to extract context from.

        """
        self.logger = logger_instance
        self.request = request
        self.context_logger: structlog.stdlib.BoundLogger | None = None

    def __enter__(self) -> structlog.stdlib.BoundLogger:
        """Enter context and bind request information to logger.

        Returns:
            structlog.stdlib.BoundLogger: Logger with request context bound.

        """
        context = {
            "method": self.request.method,
            "path": self.request.url.path,
            "correlation_id": get_correlation_id(),
            "user_agent": self.request.headers.get("user-agent", "unknown"),
        }
        self.context_logger = self.logger.bind(**context)
        return self.context_logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and log any exceptions.

        Args:
            exc_type: Exception type if an exception occurred, None otherwise.
            exc_val: Exception value if an exception occurred, None otherwise.
            exc_tb: Exception traceback if an exception occurred, None otherwise.

        """
        if exc_type is not None and self.context_logger:
            self.context_logger.error(
                "Exception in request context",
                exc_type=exc_type.__name__,
                exc_value=str(exc_val),
            )


def log_file_operation(operation: str, filename: str, file_id: str | None = None):
    """Log file operations with consistent context and tracking.

    Args:
        operation: Description of the file operation.
        filename: Name of the file being operated on.
        file_id: Optional file ID for tracking.

    Returns:
        Callable: Decorated function with file operation logging.

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
            except Exception as operation_error:
                duration = time.perf_counter() - start_time
                operation_logger.error(
                    f"Failed {operation}",
                    duration_ms=round(duration * 1000, 2),
                    error=str(operation_error),
                    error_type=type(operation_error).__name__,
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
            except Exception as operation_error:
                duration = time.perf_counter() - start_time
                operation_logger.error(
                    f"Failed {operation}",
                    duration_ms=round(duration * 1000, 2),
                    error=str(operation_error),
                    error_type=type(operation_error).__name__,
                    success=False,
                )
                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
