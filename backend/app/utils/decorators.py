"""Reusable decorator utilities for performance tracking and logging.

This module provides a unified approach to creating async/sync wrapper
decorators, eliminating code duplication across the application.
"""

import asyncio
import functools
import time
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

import structlog

P = ParamSpec("P")
R = TypeVar("R")


def create_async_sync_wrapper(
    func: Callable[P, R],
    before_call: Callable[[tuple, dict], Any] | None = None,
    after_call: Callable[[Any, float], Any] | None = None,
    on_error: Callable[[Exception, float], Any] | None = None,
) -> Callable[P, R]:
    """Create a wrapper that works for both async and sync functions.

    This factory function eliminates the need to duplicate async_wrapper
    and sync_wrapper implementations across different decorators.

    Args:
        func: The function to wrap (can be async or sync).
        before_call: Optional callback executed before function call.
            Receives (args, kwargs) and can return context data.
        after_call: Optional callback executed after successful function call.
            Receives (result, duration_seconds) and can return modified result.
        on_error: Optional callback executed when an exception occurs.
            Receives (exception, duration_seconds). Should not suppress the exception.

    Returns:
        Wrapped function that maintains async/sync nature of original function.

    Example:
        >>> def before(args, kwargs):
        ...     print(f"Starting with {args}")
        ...     return {"start_time": time.time()}
        >>>
        >>> def after(result, duration):
        ...     print(f"Completed in {duration}s")
        ...     return result
        >>>
        >>> @create_async_sync_wrapper(before_call=before, after_call=after)
        >>> async def my_async_func():
        ...     await asyncio.sleep(1)
        ...     return "done"

    """

    def _execute_wrapper_logic(
        result: R, start_time: float, exception: Exception | None = None
    ) -> None:
        """Execute common wrapper logic for success/error cases.
        
        Args:
            result: Function result (ignored if exception is provided).
            start_time: Start time for duration calculation.
            exception: Exception if an error occurred, None otherwise.
        """
        duration = time.perf_counter() - start_time

        if exception is None:
            # Success case: execute after callback
            if after_call:
                after_call(result, duration)
        else:
            # Error case: execute error callback
            if on_error:
                on_error(exception, duration)

    @functools.wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """Wrapper for async functions."""
        start_time = time.perf_counter()

        if before_call:
            before_call(args, kwargs)

        try:
            result = await func(*args, **kwargs)
            _execute_wrapper_logic(result, start_time)
            return result
        except Exception as exception:
            _execute_wrapper_logic(None, start_time, exception)  # type: ignore[arg-type]
            raise

    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """Wrapper for sync functions."""
        start_time = time.perf_counter()

        if before_call:
            before_call(args, kwargs)

        try:
            result = func(*args, **kwargs)
            _execute_wrapper_logic(result, start_time)
            return result
        except Exception as exception:
            _execute_wrapper_logic(None, start_time, exception)  # type: ignore[arg-type]
            raise

    # Return the appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper  # type: ignore[return-value]
    else:
        return sync_wrapper  # type: ignore[return-value]


def performance_logger(
    operation: str,
    logger: structlog.stdlib.BoundLogger | None = None,
    log_args: bool = False,
    log_result: bool = False,
    min_duration_ms: float = 0.0,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Unified performance logging decorator for both async and sync functions.

    This decorator consolidates the functionality of:
    - backend.app.core.logging.log_performance
    - backend.app.utils.logger.log_function_call
    - backend.app.middleware.logging.log_file_operation

    Args:
        operation: Name of the operation being performed.
        logger: Logger instance to use (defaults to module logger).
        log_args: Whether to log function arguments.
        log_result: Whether to log function result.
        min_duration_ms: Only log if duration exceeds this threshold.

    Returns:
        Decorator function.

    Example:
        >>> @performance_logger("database_query", log_args=True)
        >>> async def fetch_user(user_id: int):
        ...     return {"id": user_id, "name": "John"}

    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # Get logger for the function's module
        func_logger = logger or structlog.get_logger(func.__module__)

        def before_call(args: tuple, kwargs: dict) -> None:
            """Log operation start with optional arguments."""
            context: dict[str, Any] = {
                "operation": operation,
                "function": func.__name__,
            }

            if log_args and (args or kwargs):
                # Only log serializable args
                if args:
                    context["args"] = str(args)
                if kwargs:
                    context["kwargs"] = {
                        k: (str(v) if not hasattr(v, "__dict__") else f"<{type(v).__name__}>")
                        for k, v in kwargs.items()
                    }

            func_logger.bind(**context).info(f"Starting {operation}")

        def after_call(result: Any, duration: float) -> None:
            """Log successful completion with timing."""
            duration_ms = duration * 1000

            # Only log if duration meets threshold
            if duration_ms < min_duration_ms:
                return

            context: dict[str, Any] = {
                "operation": operation,
                "function": func.__name__,
                "duration_ms": round(duration_ms, 2),
                "success": True,
            }

            if log_result and result is not None:
                context["result_type"] = type(result).__name__

            func_logger.bind(**context).info(f"Completed {operation}")

        def on_error(exception: Exception, duration: float) -> None:
            """Log error with timing."""
            duration_ms = duration * 1000

            context: dict[str, Any] = {
                "operation": operation,
                "function": func.__name__,
                "duration_ms": round(duration_ms, 2),
                "success": False,
                "error_type": type(exception).__name__,
                "error": str(exception),
            }

            func_logger.bind(**context).error(f"Failed {operation}")

        return create_async_sync_wrapper(
            func,
            before_call=before_call,
            after_call=after_call,
            on_error=on_error,
        )

    return decorator
