"""
Common test assertion helpers for the PDF viewer test suite.

This module provides reusable helper functions for common test patterns,
reducing code duplication and improving test maintainability.
"""

import io
import uuid
from contextlib import contextmanager
from typing import Optional, Dict, Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


# ==================== API Response Assertions ====================


def assert_upload_success_response(
    response, expected_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate successful upload response structure and return data.

    Args:
        response: FastAPI TestClient response
        expected_filename: Optional expected filename to validate

    Returns:
        Dict containing response data

    Raises:
        AssertionError: If response structure is invalid
    """
    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    # Core required fields
    required_fields = ["file_id", "filename", "file_size", "mime_type", "metadata"]
    for field in required_fields:
        assert field in data, f"Missing required field '{field}' in response"

    # Pydantic v2 computed fields (if present)
    computed_fields = [
        "file_size_mb",
        "upload_age_hours",
        "upload_status",
        "processing_priority",
    ]
    for field in computed_fields:
        if field in data:
            assert (
                data[field] is not None
            ), f"Computed field '{field}' should not be None"

    # Validate file_id is a valid UUID
    assert_valid_uuid(data["file_id"])

    # Validate filename if provided
    if expected_filename:
        assert (
            data["filename"] == expected_filename
        ), f"Expected filename '{expected_filename}', got '{data['filename']}'"

    # Validate basic metadata structure
    metadata = data["metadata"]
    assert isinstance(metadata, dict), "Metadata should be a dictionary"
    assert "page_count" in metadata, "Metadata missing page_count"
    assert "file_size" in metadata, "Metadata missing file_size"
    assert "encrypted" in metadata, "Metadata missing encrypted"

    return data


def assert_error_response(
    response,
    expected_status: int,
    expected_message_contains: Optional[str] = None,
    expected_error_code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate error response structure and return data.

    Args:
        response: FastAPI TestClient response
        expected_status: Expected HTTP status code
        expected_message_contains: Optional text that should be in error message
        expected_error_code: Optional specific error code to validate

    Returns:
        Dict containing error response data

    Raises:
        AssertionError: If error response structure is invalid
    """
    assert (
        response.status_code == expected_status
    ), f"Expected {expected_status}, got {response.status_code}: {response.text}"
    data = response.json()

    # FastAPI error responses always have 'detail'
    assert "detail" in data, "Error response missing 'detail' field"
    assert isinstance(data["detail"], str), "Error detail should be a string"
    assert len(data["detail"]) > 0, "Error detail should not be empty"

    # Check if expected message is contained in detail
    if expected_message_contains:
        assert (
            expected_message_contains.lower() in data["detail"].lower()
        ), f"Expected '{expected_message_contains}' in error message '{data['detail']}'"

    # Check for specific error code if provided
    if expected_error_code and "error_code" in data:
        assert (
            data["error_code"] == expected_error_code
        ), f"Expected error code '{expected_error_code}', got '{data.get('error_code')}'"

    return data


def assert_metadata_response(
    response, expected_pages: Optional[int] = None
) -> Dict[str, Any]:
    """
    Validate metadata response structure and return data.

    Args:
        response: FastAPI TestClient response
        expected_pages: Optional expected page count

    Returns:
        Dict containing metadata response data

    Raises:
        AssertionError: If metadata response structure is invalid
    """
    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    # Required metadata fields
    required_fields = ["page_count", "file_size", "encrypted"]
    for field in required_fields:
        assert field in data, f"Missing required metadata field '{field}'"

    # Validate data types
    assert isinstance(data["page_count"], int), "page_count should be an integer"
    assert isinstance(data["file_size"], int), "file_size should be an integer"
    assert isinstance(data["encrypted"], bool), "encrypted should be a boolean"

    # Validate ranges
    assert data["page_count"] > 0, "page_count should be positive"
    assert data["file_size"] > 0, "file_size should be positive"

    # Check expected pages if provided
    if expected_pages is not None:
        assert (
            data["page_count"] == expected_pages
        ), f"Expected {expected_pages} pages, got {data['page_count']}"

    return data


# ==================== PDF File Helpers ====================


def create_upload_file_data(
    filename: str, content: bytes, content_type: str = "application/pdf"
) -> Dict[str, Any]:
    """
    Create upload file data structure for multipart form.

    Args:
        filename: Name of the file
        content: File content as bytes
        content_type: MIME type of the file

    Returns:
        Dict suitable for TestClient file upload
    """
    return {"file": (filename, io.BytesIO(content), content_type)}


def upload_pdf_file(
    client: TestClient,
    filename: str,
    content: bytes,
    headers: Optional[Dict[str, str]] = None,
):
    """
    Upload a PDF file and return response.

    Args:
        client: FastAPI TestClient
        filename: Name of the PDF file
        content: PDF content as bytes
        headers: Optional additional headers

    Returns:
        Response from upload endpoint
    """
    files = create_upload_file_data(filename, content)
    return client.post("/api/upload", files=files, headers=headers or {})


def assert_valid_pdf_content(content: bytes) -> bool:
    """
    Validate PDF content characteristics.

    Args:
        content: PDF content as bytes

    Returns:
        True if content appears to be a valid PDF

    Raises:
        AssertionError: If content is not valid PDF format
    """
    assert isinstance(content, bytes), "PDF content should be bytes"
    assert len(content) > 0, "PDF content should not be empty"
    assert content.startswith(
        b"%PDF"
    ), f"Content should start with PDF header, got: {content[:10]}"

    # Additional basic PDF validation
    assert b"%%EOF" in content or content.endswith(
        b"%%EOF"
    ), "PDF should contain EOF marker"

    return True


# ==================== Field Validation Helpers ====================


def assert_valid_uuid(uuid_string: str, version: int = 4) -> uuid.UUID:
    """
    Validate UUID format and version.

    Args:
        uuid_string: String to validate as UUID
        version: Expected UUID version (default: 4)

    Returns:
        UUID object if valid

    Raises:
        AssertionError: If UUID is invalid or wrong version
    """
    try:
        uuid_obj = uuid.UUID(uuid_string)
        if version:
            assert (
                uuid_obj.version == version
            ), f"Expected UUID version {version}, got {uuid_obj.version}"
        return uuid_obj
    except ValueError as e:
        pytest.fail(f"Invalid UUID format: '{uuid_string}' - {e}")


def assert_correlation_id_propagated(response, expected_correlation_id: str) -> str:
    """
    Validate correlation ID propagation in response headers.

    Args:
        response: HTTP response object
        expected_correlation_id: Expected correlation ID value

    Returns:
        Actual correlation ID from response

    Raises:
        AssertionError: If correlation ID is missing or doesn't match
    """
    correlation_header = "x-correlation-id"
    actual_id = response.headers.get(correlation_header)

    assert actual_id is not None, f"Missing '{correlation_header}' header in response"
    assert (
        actual_id == expected_correlation_id
    ), f"Expected correlation ID '{expected_correlation_id}', got '{actual_id}'"

    return actual_id


def assert_file_size_fields(
    data: Dict[str, Any],
    expected_bytes: Optional[int] = None,
    expected_mb: Optional[float] = None,
) -> None:
    """
    Validate file size related fields for consistency.

    Args:
        data: Response data containing file size fields
        expected_bytes: Optional expected file size in bytes
        expected_mb: Optional expected file size in MB

    Raises:
        AssertionError: If file size fields are invalid or inconsistent
    """
    # Check required fields exist
    assert "file_size" in data, "Missing 'file_size' field"
    assert isinstance(data["file_size"], int), "file_size should be an integer"
    assert data["file_size"] > 0, "file_size should be positive"

    # Check computed MB field if present
    if "file_size_mb" in data:
        assert isinstance(
            data["file_size_mb"], (int, float)
        ), "file_size_mb should be numeric"

        # Validate consistency between bytes and MB
        calculated_mb = data["file_size"] / (1024 * 1024)
        assert (
            abs(data["file_size_mb"] - calculated_mb) < 0.01
        ), f"Inconsistent file sizes: {data['file_size']} bytes != {data['file_size_mb']} MB"

    # Validate expected values if provided
    if expected_bytes is not None:
        assert (
            data["file_size"] == expected_bytes
        ), f"Expected {expected_bytes} bytes, got {data['file_size']}"

    if expected_mb is not None and "file_size_mb" in data:
        assert (
            abs(data["file_size_mb"] - expected_mb) < 0.01
        ), f"Expected {expected_mb} MB, got {data['file_size_mb']}"


def assert_timestamp_fields(data: Dict[str, Any], *field_names: str) -> None:
    """
    Validate timestamp fields are present and properly formatted.

    Args:
        data: Response data containing timestamp fields
        field_names: Names of timestamp fields to validate

    Raises:
        AssertionError: If timestamp fields are invalid
    """
    from datetime import datetime

    for field_name in field_names:
        if field_name in data:
            timestamp = data[field_name]
            assert isinstance(timestamp, str), f"{field_name} should be a string"

            # Try to parse as ISO format
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError as e:
                pytest.fail(
                    f"Invalid timestamp format in {field_name}: {timestamp} - {e}"
                )


# ==================== Mock Helpers ====================


@contextmanager
def mock_pdf_service_method(method_name: str, side_effect=None, return_value=None):
    """
    Context manager to mock PDFService methods.

    Args:
        method_name: Name of the method to mock
        side_effect: Optional exception or function to raise/call
        return_value: Optional return value for the method

    Yields:
        Mock object for the method
    """
    patch_target = f"backend.app.services.pdf_service.PDFService.{method_name}"

    with patch(patch_target) as mock_method:
        if side_effect is not None:
            mock_method.side_effect = side_effect
        elif return_value is not None:
            mock_method.return_value = return_value

        yield mock_method


@contextmanager
def mock_api_dependency(dependency_path: str, mock_return=None):
    """
    Context manager to mock API dependencies.

    Args:
        dependency_path: Full import path to the dependency
        mock_return: Optional return value for the dependency

    Yields:
        Mock object for the dependency
    """
    with patch(dependency_path) as mock_dep:
        if mock_return is not None:
            mock_dep.return_value = mock_return
        yield mock_dep


# ==================== Test Workflow Helpers ====================


def perform_upload_workflow(
    client: TestClient, filename: str, content: bytes, expect_success: bool = True
) -> Dict[str, Any]:
    """
    Perform complete upload workflow and validate response.

    Args:
        client: FastAPI TestClient
        filename: Name of file to upload
        content: File content as bytes
        expect_success: Whether to expect successful upload

    Returns:
        Response data from upload

    Raises:
        AssertionError: If workflow doesn't behave as expected
    """
    response = upload_pdf_file(client, filename, content)

    if expect_success:
        return assert_upload_success_response(response, filename)
    else:
        # For error cases, caller should specify expected status
        assert (
            response.status_code != 200
        ), f"Expected upload to fail, but got 200: {response.text}"
        return response.json()


def perform_metadata_workflow(
    client: TestClient,
    file_id: str,
    expect_success: bool = True,
    expected_pages: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Perform metadata retrieval workflow and validate response.

    Args:
        client: FastAPI TestClient
        file_id: ID of file to get metadata for
        expect_success: Whether to expect successful retrieval
        expected_pages: Optional expected page count

    Returns:
        Metadata response data

    Raises:
        AssertionError: If workflow doesn't behave as expected
    """
    response = client.get(f"/api/metadata/{file_id}")

    if expect_success:
        return assert_metadata_response(response, expected_pages)
    else:
        assert (
            response.status_code != 200
        ), "Expected metadata retrieval to fail, but got 200"
        return response.json()


def perform_full_pdf_workflow(
    client: TestClient, filename: str, content: bytes, cleanup: bool = True
) -> Dict[str, Any]:
    """
    Perform complete PDF workflow: upload → metadata → retrieve → delete.

    Args:
        client: FastAPI TestClient
        filename: Name of file to upload
        content: File content as bytes
        cleanup: Whether to delete file at the end

    Returns:
        Dict with results from each step

    Raises:
        AssertionError: If any step fails unexpectedly
    """
    results = {}

    # Step 1: Upload
    results["upload"] = perform_upload_workflow(client, filename, content)
    file_id = results["upload"]["file_id"]

    # Step 2: Get metadata
    expected_pages = results["upload"]["metadata"]["page_count"]
    results["metadata"] = perform_metadata_workflow(
        client, file_id, expected_pages=expected_pages
    )

    # Step 3: Retrieve PDF
    retrieve_response = client.get(f"/api/pdf/{file_id}")
    assert (
        retrieve_response.status_code == 200
    ), f"Failed to retrieve PDF: {retrieve_response.text}"
    assert retrieve_response.headers["content-type"] == "application/pdf"
    results["retrieve"] = {
        "status": "success",
        "content_length": len(retrieve_response.content),
    }

    # Step 4: Delete (if cleanup requested)
    if cleanup:
        delete_response = client.delete(f"/api/pdf/{file_id}")
        assert (
            delete_response.status_code == 200
        ), f"Failed to delete PDF: {delete_response.text}"
        results["delete"] = {"status": "success"}

    return results
