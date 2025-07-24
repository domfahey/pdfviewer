"""
Mock helpers for standardizing mock strategies across the test suite.

This module provides reusable mock patterns and strategies to improve
test consistency and reduce mock-related code duplication.
"""

import uuid
from contextlib import contextmanager, ExitStack
from pathlib import Path
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, patch

from tests.config import TestConstants


class MockResponseBuilder:
    """Builder for creating consistent mock responses."""

    def __init__(self):
        self._response_data = {}
        self._status_code = 200
        self._headers = {}

    def with_status(self, status_code: int) -> "MockResponseBuilder":
        """Set the response status code."""
        self._status_code = status_code
        return self

    def with_data(self, **data: Any) -> "MockResponseBuilder":
        """Add data to the response."""
        self._response_data.update(data)
        return self

    def with_header(self, key: str, value: str) -> "MockResponseBuilder":
        """Add a header to the response."""
        self._headers[key] = value
        return self

    def with_correlation_id(
        self, correlation_id: Optional[str] = None
    ) -> "MockResponseBuilder":
        """Add correlation ID header."""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        return self.with_header("x-correlation-id", correlation_id)

    def build(self) -> Mock:
        """Build the mock response object."""
        mock_response = Mock()
        mock_response.status_code = self._status_code
        mock_response.json.return_value = self._response_data
        mock_response.text = str(self._response_data)
        mock_response.content = str(self._response_data).encode()
        mock_response.headers = self._headers
        return mock_response


class PDFServiceMockBuilder:
    """Builder for creating PDFService mocks with common configurations."""

    def __init__(self):
        self._service_mock = Mock()
        self._upload_dir = "test_uploads"
        self._file_metadata = {}
        self._logger_mock = None

    def with_upload_dir(self, upload_dir: str) -> "PDFServiceMockBuilder":
        """Set the upload directory."""
        self._upload_dir = upload_dir
        return self

    def with_file_metadata(
        self, file_id: str, metadata: Dict[str, Any]
    ) -> "PDFServiceMockBuilder":
        """Add file metadata for a specific file ID."""
        self._file_metadata[file_id] = metadata
        return self

    def with_upload_success(
        self, file_id: Optional[str] = None
    ) -> "PDFServiceMockBuilder":
        """Configure successful upload behavior."""
        if file_id is None:
            file_id = str(uuid.uuid4())

        upload_response = {
            "file_id": file_id,
            "filename": "test.pdf",
            "file_size": TestConstants.MEDIUM_FILE_SIZE,
            "mime_type": "application/pdf",
            "metadata": {
                "page_count": 1,
                "file_size": TestConstants.MEDIUM_FILE_SIZE,
                "encrypted": False,
            },
        }

        self._service_mock.upload_pdf.return_value = upload_response
        return self

    def with_upload_failure(self, exception: Exception) -> "PDFServiceMockBuilder":
        """Configure upload failure behavior."""
        self._service_mock.upload_pdf.side_effect = exception
        return self

    def with_metadata_success(
        self, file_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> "PDFServiceMockBuilder":
        """Configure successful metadata retrieval."""
        if metadata is None:
            metadata = {
                "page_count": 1,
                "file_size": TestConstants.MEDIUM_FILE_SIZE,
                "encrypted": False,
            }

        def get_metadata_side_effect(requested_file_id: str):
            if requested_file_id == file_id:
                return metadata
            else:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="File not found")

        self._service_mock.get_pdf_metadata.side_effect = get_metadata_side_effect
        return self

    def with_metadata_failure(
        self, file_id: str, exception: Exception
    ) -> "PDFServiceMockBuilder":
        """Configure metadata retrieval failure."""

        def get_metadata_side_effect(requested_file_id: str):
            if requested_file_id == file_id:
                raise exception
            else:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="File not found")

        self._service_mock.get_pdf_metadata.side_effect = get_metadata_side_effect
        return self

    def with_file_retrieval_success(
        self, file_id: str, file_path: Optional[str] = None
    ) -> "PDFServiceMockBuilder":
        """Configure successful file retrieval."""
        if file_path is None:
            file_path = f"/tmp/test_uploads/{file_id}.pdf"

        def get_path_side_effect(requested_file_id: str):
            if requested_file_id == file_id:
                return file_path
            else:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="File not found")

        self._service_mock.get_pdf_path.side_effect = get_path_side_effect
        return self

    def with_file_retrieval_failure(
        self, file_id: str, exception: Exception
    ) -> "PDFServiceMockBuilder":
        """Configure file retrieval failure."""

        def get_path_side_effect(requested_file_id: str):
            if requested_file_id == file_id:
                raise exception
            else:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="File not found")

        self._service_mock.get_pdf_path.side_effect = get_path_side_effect
        return self

    def with_delete_success(self, file_id: str) -> "PDFServiceMockBuilder":
        """Configure successful file deletion."""

        def delete_side_effect(requested_file_id: str):
            return requested_file_id == file_id

        self._service_mock.delete_pdf.side_effect = delete_side_effect
        return self

    def with_delete_failure(self, file_id: str) -> "PDFServiceMockBuilder":
        """Configure file deletion failure."""

        def delete_side_effect(requested_file_id: str):
            if requested_file_id == file_id:
                return False
            else:
                return True  # Other files can be deleted successfully

        self._service_mock.delete_pdf.side_effect = delete_side_effect
        return self

    def with_logging_mock(self) -> Mock:
        """Configure mock logger for testing logging behavior."""
        self._logger_mock = Mock()
        self._logger_mock.info = Mock()
        self._logger_mock.error = Mock()
        self._logger_mock.warning = Mock()
        self._logger_mock.debug = Mock()
        return self._logger_mock

    def build(self) -> Mock:
        """Build the PDFService mock."""
        self._service_mock.upload_dir = self._upload_dir
        return self._service_mock


# ==================== Common Mock Patterns ====================


@contextmanager
def mock_pdfservice_with_behavior(behavior_config: Dict[str, Any]):
    """
    Context manager for mocking PDFService with specific behavior.

    Args:
        behavior_config: Configuration dict specifying mock behavior

    Example:
        behavior_config = {
            "upload": {"success": True, "file_id": "test-id"},
            "metadata": {"success": True, "pages": 5},
            "retrieve": {"success": False, "exception": HTTPException(404)},
            "delete": {"success": True}
        }
    """
    builder = PDFServiceMockBuilder()

    # Configure upload behavior
    if "upload" in behavior_config:
        upload_config = behavior_config["upload"]
        if upload_config.get("success", True):
            builder.with_upload_success(upload_config.get("file_id"))
        else:
            exception = upload_config.get("exception", Exception("Upload failed"))
            builder.with_upload_failure(exception)

    # Configure metadata behavior
    if "metadata" in behavior_config:
        metadata_config = behavior_config["metadata"]
        file_id = metadata_config.get("file_id", "test-file-id")

        if metadata_config.get("success", True):
            metadata = {
                "page_count": metadata_config.get("pages", 1),
                "file_size": metadata_config.get(
                    "file_size", TestConstants.MEDIUM_FILE_SIZE
                ),
                "encrypted": metadata_config.get("encrypted", False),
            }
            builder.with_metadata_success(file_id, metadata)
        else:
            exception = metadata_config.get(
                "exception", Exception("Metadata extraction failed")
            )
            builder.with_metadata_failure(file_id, exception)

    # Configure retrieve behavior
    if "retrieve" in behavior_config:
        retrieve_config = behavior_config["retrieve"]
        file_id = retrieve_config.get("file_id", "test-file-id")

        if retrieve_config.get("success", True):
            file_path = retrieve_config.get("file_path")
            builder.with_file_retrieval_success(file_id, file_path)
        else:
            exception = retrieve_config.get(
                "exception", Exception("File retrieval failed")
            )
            builder.with_file_retrieval_failure(file_id, exception)

    # Configure delete behavior
    if "delete" in behavior_config:
        delete_config = behavior_config["delete"]
        file_id = delete_config.get("file_id", "test-file-id")

        if delete_config.get("success", True):
            builder.with_delete_success(file_id)
        else:
            builder.with_delete_failure(file_id)

    service_mock = builder.build()

    with patch("backend.app.api.pdf.get_pdf_service", return_value=service_mock):
        yield service_mock


@contextmanager
def mock_external_requests(responses: List[Dict[str, Any]]):
    """
    Context manager for mocking external HTTP requests.

    Args:
        responses: List of response configurations

    Example:
        responses = [
            {"url": "http://example.com/test.pdf", "status": 200, "content": b"pdf content"},
            {"url": "http://example.com/error", "status": 404, "content": b"Not found"}
        ]
    """

    def mock_get_side_effect(url, **kwargs):
        for response_config in responses:
            if response_config["url"] == url:
                mock_response = Mock()
                mock_response.status_code = response_config.get("status", 200)
                mock_response.content = response_config.get("content", b"")
                mock_response.headers = response_config.get("headers", {})
                mock_response.raise_for_status = Mock()

                if mock_response.status_code >= 400:
                    mock_response.raise_for_status.side_effect = Exception(
                        f"HTTP {mock_response.status_code}"
                    )

                return mock_response

        # Default to 404 for unknown URLs
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.content = b"Not found"
        mock_response.raise_for_status.side_effect = Exception("HTTP 404")
        return mock_response

    with patch("requests.get", side_effect=mock_get_side_effect):
        yield


@contextmanager
def mock_file_operations(file_operations: Dict[str, Any]):
    """
    Context manager for mocking file system operations.

    Args:
        file_operations: Configuration for file operations

    Example:
        file_operations = {
            "exists": {"/path/to/file.pdf": True, "/path/to/missing.pdf": False},
            "read": {"/path/to/file.pdf": b"pdf content"},
            "write": {"allow": True},
            "delete": {"allow": True}
        }
    """

    # Mock pathlib.Path operations
    def mock_exists_side_effect(path_str: str) -> bool:
        exists_config = file_operations.get("exists", {})
        return exists_config.get(str(path_str), False)

    def mock_read_bytes_side_effect(path_str: str) -> bytes:
        read_config = file_operations.get("read", {})
        if str(path_str) in read_config:
            return read_config[str(path_str)]
        else:
            raise FileNotFoundError(f"File not found: {path_str}")

    def mock_write_bytes_side_effect(path_str: str, content: bytes) -> None:
        write_config = file_operations.get("write", {"allow": True})
        if not write_config.get("allow", True):
            raise PermissionError(f"Write not allowed: {path_str}")

    def mock_unlink_side_effect(path_str: str) -> None:
        delete_config = file_operations.get("delete", {"allow": True})
        if not delete_config.get("allow", True):
            raise PermissionError(f"Delete not allowed: {path_str}")

    # Apply patches using ExitStack for better context management
    with ExitStack() as stack:
        # Create wrapper functions that properly handle the 'self' parameter
        def exists_wrapper(self):
            return mock_exists_side_effect(str(self))
        
        def read_bytes_wrapper(self):
            return mock_read_bytes_side_effect(str(self))
        
        def write_bytes_wrapper(self, content):
            return mock_write_bytes_side_effect(str(self), content)
        
        def unlink_wrapper(self):
            return mock_unlink_side_effect(str(self))
        
        stack.enter_context(patch.object(Path, "exists", exists_wrapper))
        stack.enter_context(patch.object(Path, "read_bytes", read_bytes_wrapper))
        stack.enter_context(patch.object(Path, "write_bytes", write_bytes_wrapper))
        stack.enter_context(patch.object(Path, "unlink", unlink_wrapper))
        yield


# ==================== Specialized Mock Factories ====================


def create_mock_logger():
    """Create a mock logger with standard logging methods."""
    mock_logger = Mock()

    # Standard logging methods
    for level in ["debug", "info", "warning", "error", "critical"]:
        setattr(mock_logger, level, Mock())

    # Structured logging methods if present
    mock_logger.bind = Mock(return_value=mock_logger)
    mock_logger.with_context = Mock(return_value=mock_logger)

    return mock_logger


def create_mock_performance_tracker():
    """Create a mock performance tracker with standard methods."""
    mock_tracker = Mock()

    # Performance tracking methods
    mock_tracker.start = Mock()
    mock_tracker.stop = Mock()
    mock_tracker.duration = 1.25  # Default duration in seconds

    # Context manager support
    mock_tracker.__enter__ = Mock(return_value=mock_tracker)
    mock_tracker.__exit__ = Mock(return_value=None)

    return mock_tracker


def create_mock_api_logger():
    """Create a mock API logger with standard logging methods."""
    mock_api_logger = Mock()

    # API logging methods
    logging_methods = [
        "log_request_received",
        "log_validation_start",
        "log_validation_success",
        "log_validation_error",
        "log_processing_start",
        "log_processing_success",
        "log_processing_error",
        "log_response_sent",
    ]

    for method in logging_methods:
        setattr(mock_api_logger, method, Mock())

    return mock_api_logger


# ==================== Error Simulation Helpers ====================


class ErrorSimulator:
    """Helper class for simulating different types of errors."""

    @staticmethod
    def network_timeout():
        """Create a network timeout exception."""
        import requests

        return requests.exceptions.Timeout("Connection timed out")

    @staticmethod
    def network_connection_error():
        """Create a network connection error."""
        import requests

        return requests.exceptions.ConnectionError("Connection failed")

    @staticmethod
    def file_not_found(filename: str = "test.pdf"):
        """Create a file not found error."""
        return FileNotFoundError(f"File not found: {filename}")

    @staticmethod
    def permission_denied(operation: str = "access"):
        """Create a permission denied error."""
        return PermissionError(f"Permission denied: {operation}")

    @staticmethod
    def invalid_pdf_error():
        """Create an invalid PDF error."""
        return ValueError("Invalid PDF format")

    @staticmethod
    def http_error(status_code: int, message: str = "HTTP Error"):
        """Create an HTTP error."""
        from fastapi import HTTPException

        return HTTPException(status_code=status_code, detail=message)

    @staticmethod
    def database_error():
        """Create a database error."""
        return Exception("Database connection failed")


# ==================== Mock File Helpers ====================


def create_mock_upload_file(
    filename: str = "test.pdf",
    content_type: str = "application/pdf",
    file_size: int = 1024,
    file_content: bytes = b"mock pdf content",
) -> Mock:
    """
    Create a mock UploadFile object with specified properties.

    Args:
        filename: The filename to set
        content_type: The MIME type to set
        file_size: The file size to set
        file_content: The file content to return from read()

    Returns:
        Mock UploadFile object ready for testing
    """
    from fastapi import UploadFile

    mock_file = Mock(spec=UploadFile)
    mock_file.filename = filename
    mock_file.content_type = content_type
    mock_file.size = file_size

    # Make read() async
    async def mock_read():
        return file_content

    mock_file.read = mock_read

    return mock_file


def create_mock_pdf_file_batch(count: int = 3, base_name: str = "test") -> List[Mock]:
    """
    Create multiple mock UploadFile objects for batch testing.

    Args:
        count: Number of mock files to create
        base_name: Base name for the files (will be numbered)

    Returns:
        List of mock UploadFile objects
    """
    files = []
    for i in range(count):
        filename = f"{base_name}_{i + 1}.pdf"
        content = f"mock pdf content {i + 1}".encode()
        mock_file = create_mock_upload_file(
            filename=filename, file_size=len(content), file_content=content
        )
        files.append(mock_file)

    return files


# ==================== Mock Validation Helpers ====================


def assert_mock_called_with_correlation_id(mock_obj: Mock, correlation_id: str) -> None:
    """
    Assert that a mock was called with a specific correlation ID.

    Args:
        mock_obj: Mock object to check
        correlation_id: Expected correlation ID

    Raises:
        AssertionError: If mock wasn't called with correlation ID
    """
    mock_obj.assert_called()

    # Check if correlation ID was passed in any call
    found_correlation_id = False
    for call in mock_obj.call_args_list:
        args, kwargs = call

        # Check in kwargs
        if "correlation_id" in kwargs and kwargs["correlation_id"] == correlation_id:
            found_correlation_id = True
            break

        # Check in positional args (less common but possible)
        if correlation_id in args:
            found_correlation_id = True
            break

    assert (
        found_correlation_id
    ), f"Mock was not called with correlation_id '{correlation_id}'"


def assert_mock_called_with_file_context(
    mock_obj: Mock, filename: str, file_size: Optional[int] = None
) -> None:
    """
    Assert that a mock was called with file context information.

    Args:
        mock_obj: Mock object to check
        filename: Expected filename
        file_size: Optional expected file size

    Raises:
        AssertionError: If mock wasn't called with file context
    """
    mock_obj.assert_called()

    found_file_context = False
    for call in mock_obj.call_args_list:
        args, kwargs = call

        # Check for filename in kwargs
        if "filename" in kwargs and kwargs["filename"] == filename:
            found_file_context = True

            # Check file size if provided
            if file_size is not None and "file_size" in kwargs:
                assert (
                    kwargs["file_size"] == file_size
                ), f"Expected file_size {file_size}, got {kwargs['file_size']}"
            break

    assert found_file_context, f"Mock was not called with filename '{filename}'"


# ==================== Additional Mock Utilities ====================


class MockFileHelper:
    """Helper for mocking file operations and uploads."""

    @staticmethod
    def create_mock_upload_file(
        filename: str, content: bytes, content_type: str = "application/pdf"
    ):
        """Create a mock UploadFile object."""
        from fastapi import UploadFile
        from io import BytesIO

        file_obj = BytesIO(content)
        upload_file = UploadFile(
            filename=filename, file=file_obj, headers={"content-type": content_type}
        )
        return upload_file

    @staticmethod
    def create_mock_file_response(filename: str, file_size: int, content: bytes = None):
        """Create a mock file response."""
        if content is None:
            content = b"PDF mock content" * (file_size // 16 + 1)
            content = content[:file_size]

        mock_response = Mock()
        mock_response.filename = filename
        mock_response.file_size = file_size
        mock_response.content = content
        mock_response.read.return_value = content
        return mock_response


def simulate_service_error(error_type: str, **kwargs):
    """Simulate different types of service errors."""
    if error_type == "timeout":
        return ErrorSimulator.network_timeout()
    elif error_type == "connection":
        return ErrorSimulator.network_connection_error()
    elif error_type == "file_not_found":
        return ErrorSimulator.file_not_found(kwargs.get("filename", "test.pdf"))
    elif error_type == "permission":
        return ErrorSimulator.permission_denied(kwargs.get("operation", "access"))
    elif error_type == "invalid_pdf":
        return ErrorSimulator.invalid_pdf_error()
    elif error_type == "http":
        return ErrorSimulator.http_error(
            kwargs.get("status_code", 500),
            kwargs.get("message", "Internal Server Error"),
        )
    elif error_type == "database":
        return ErrorSimulator.database_error()
    else:
        return Exception(f"Unknown error type: {error_type}")
