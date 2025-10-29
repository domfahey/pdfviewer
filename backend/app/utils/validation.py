"""Common validation utilities for API endpoints."""

from fastapi import HTTPException

# Public API
__all__ = [
    "validate_file_id",
    "validate_required_string",
]


def validate_file_id(file_id: str) -> str:
    """Validate that a file ID is not empty.
    
    Args:
        file_id: The file ID to validate
        
    Returns:
        str: The validated file ID (stripped)
        
    Raises:
        HTTPException: If file ID is empty or only whitespace
    """
    if not file_id or not file_id.strip():
        raise HTTPException(status_code=400, detail="File ID is required")
    
    return file_id.strip()


def validate_required_string(
    value: str | None,
    field_name: str,
) -> str:
    """Validate that a required string field is not empty.
    
    Args:
        value: The value to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        str: The validated value (stripped)
        
    Raises:
        HTTPException: If value is None, empty or only whitespace
    """
    if not value or not value.strip():
        error_msg = f"{field_name} is required"
        raise HTTPException(status_code=400, detail=error_msg)
    
    return value.strip()
