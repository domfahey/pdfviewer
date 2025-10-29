"""Common validation utilities for API endpoints."""

from typing import Any

from fastapi import HTTPException

from .api_logging import APILogger

# Public API
__all__ = [
    "validate_file_id",
    "validate_required_string",
]


def validate_file_id(file_id: str, api_logger: APILogger | None = None) -> str:
    """Validate that a file ID is not empty.
    
    Args:
        file_id: The file ID to validate
        api_logger: Optional APILogger instance for logging validation errors
        
    Returns:
        str: The validated file ID (stripped)
        
    Raises:
        HTTPException: If file ID is empty or only whitespace
    """
    if not file_id or not file_id.strip():
        if api_logger:
            api_logger.log_validation_error("Empty file_id provided")
        raise HTTPException(status_code=400, detail="File ID is required")
    
    return file_id.strip()


def validate_required_string(
    value: str | None,
    field_name: str,
    api_logger: APILogger | None = None,
) -> str:
    """Validate that a required string field is not empty.
    
    Args:
        value: The value to validate
        field_name: Name of the field (for error messages)
        api_logger: Optional APILogger instance for logging validation errors
        
    Returns:
        str: The validated value (stripped)
        
    Raises:
        HTTPException: If value is None, empty or only whitespace
    """
    if not value or not value.strip():
        error_msg = f"{field_name} is required"
        if api_logger:
            api_logger.log_validation_error(f"Empty {field_name} provided", **{field_name: value})
        raise HTTPException(status_code=400, detail=error_msg)
    
    return value.strip()
