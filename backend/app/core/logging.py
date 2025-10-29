"""
Centralized logging configuration for the PDF Viewer API.

This module provides structured logging with context, correlation IDs,
and different output formats for development vs production environments.
"""

import logging
import logging.config
import sys
from typing import Any

import structlog
from rich.console import Console
from rich.logging import RichHandler


def configure_logging(
    level: str = "INFO",
    json_logs: bool = False,
    enable_correlation_id: bool = True,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output logs in JSON format (for production)
        enable_correlation_id: Whether to add correlation IDs to logs
    """
    log_level = getattr(logging, level.upper())

    # Configure timestamper
    timestamper = structlog.processors.TimeStamper(fmt="ISO")

    # Base processors for all logs
    shared_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add correlation ID processor if enabled
    if enable_correlation_id:
        from ..middleware.logging import add_correlation_id

        shared_processors.insert(0, add_correlation_id)

    if json_logs:
        # Production: JSON output
        structlog.configure(
            processors=shared_processors
            + [
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Configure standard library logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=log_level,
        )
    else:
        # Development: Rich console output
        structlog.configure(
            processors=shared_processors + [structlog.dev.ConsoleRenderer(colors=True)],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Configure rich handler for beautiful console output
        console = Console(stderr=True)
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_level=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True,
        )

        logging.basicConfig(
            level=log_level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[rich_handler],
        )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def setup_uvicorn_logging(log_level: str = "INFO") -> dict[str, Any]:
    """
    Configure uvicorn logging to work with our structured logging.

    Args:
        log_level: Log level for uvicorn

    Returns:
        Uvicorn logging configuration dict
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=True),
            },
            "access": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=True),
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.error": {"level": log_level},
            "uvicorn.access": {
                "handlers": ["access"],
                "level": log_level,
                "propagate": False,
            },
        },
    }


class LogContext:
    """Context manager for adding structured log context."""

    def __init__(self, logger: structlog.stdlib.BoundLogger, **context: Any) -> None:
        self.logger = logger
        self.context = context
        self.bound_logger: structlog.stdlib.BoundLogger | None = None

    def __enter__(self) -> structlog.stdlib.BoundLogger:
        self.bound_logger = self.logger.bind(**self.context)
        return self.bound_logger

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None and self.bound_logger:
            self.bound_logger.error(
                "Exception occurred in log context",
                exc_type=exc_type.__name__,
                exc_value=str(exc_val),
            )


# Performance monitoring decorators
def log_performance(operation: str):
    """Decorator to log function performance metrics."""

    def decorator(func):
        import functools
        import time

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.perf_counter()

            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                logger.info(
                    f"{operation} completed",
                    operation=operation,
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2),
                    success=True,
                )
                return result
            except Exception as e:
                duration = time.perf_counter() - start_time
                logger.error(
                    f"{operation} failed",
                    operation=operation,
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2),
                    error=str(e),
                    success=False,
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                logger.info(
                    f"{operation} completed",
                    operation=operation,
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2),
                    success=True,
                )
                return result
            except Exception as e:
                duration = time.perf_counter() - start_time
                logger.error(
                    f"{operation} failed",
                    operation=operation,
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2),
                    error=str(e),
                    success=False,
                )
                raise

        # Return appropriate wrapper based on whether function is async
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
