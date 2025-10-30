"""Common validation utilities for API endpoints."""

from fastapi import HTTPException

# Public API
__all__ = [
    "validate_file_id",
    "validate_required_string",
    "api_endpoint_handler",
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


@contextmanager
def api_endpoint_handler(
    operation: str,
    file_id: str | None = None,
    default_error_message: str = "Operation failed",
):
    """Context manager for common API endpoint workflow.
    
    Handles the standard pattern of:
    1. Request logging
    2. Validation (with file_id if provided)
    3. Processing
    4. Error handling
    
    Args:
        operation: Name of the API operation (e.g., "pdf_retrieve")
        file_id: Optional file ID to validate
        default_error_message: Default error message for non-HTTP exceptions
        
    Yields:
        APILogger: Configured logger for the operation
        
    Example:
        >>> with api_endpoint_handler("pdf_retrieve", file_id=file_id) as logger:
        ...     file_path = pdf_service.get_pdf_path(file_id)
        ...     logger.log_processing_success(file_id=file_id, file_path=str(file_path))
        ...     return FileResponse(path=str(file_path))
    """
    api_logger = APILogger(operation)
    
    # Build context for logging
    context: dict[str, Any] = {}
    if file_id:
        context["file_id"] = file_id
    
    # Log request received
    api_logger.log_request_received(**context)
    api_logger.log_validation_start()
    
    # Validate file_id if provided
    if file_id:
        validate_file_id(file_id, api_logger)
        api_logger.log_validation_success(**context)
    
    api_logger.log_processing_start(**context)
    
    try:
        yield api_logger
    except HTTPException as http_error:
        api_logger.log_processing_error(
            http_error,
            status_code=http_error.status_code,
            **context
        )
        raise
    except Exception as error:
        api_logger.log_processing_error(error, **context)
        raise HTTPException(
            status_code=500,
            detail=f"{default_error_message}: {str(error)}"
        )
