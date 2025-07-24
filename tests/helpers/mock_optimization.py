"""
Optimized mock helpers for performance-critical test scenarios.

This module provides pre-configured mocks and optimization utilities
to reduce test execution time while maintaining test reliability.
"""

import asyncio
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, Mock

import pytest


class OptimizedPDFMocks:
    """Pre-configured mocks for PDF processing operations."""

    @staticmethod
    def mock_pdf_service():
        """Mock PDF service with optimized responses."""
        mock_service = Mock()

        # Mock file validation (fast)
        mock_service.validate_pdf_file.return_value = True

        # Mock metadata extraction (fast)
        mock_service.extract_metadata.return_value = {
            "page_count": 1,
            "file_size": 1024,
            "encrypted": False,
            "creation_date": "2024-01-01T12:00:00Z",
            "modification_date": "2024-01-01T12:00:00Z",
        }

        # Mock page rendering (fast)
        mock_service.render_page.return_value = b"\x89PNG\r\n\x1a\n" + b"mock_png_data"

        # Mock analysis (fast)
        mock_service.analyze_document.return_value = {
            "document_id": str(uuid.uuid4()),
            "total_pages": 1,
            "extracted_fields": {"test": "data"},
            "confidence_scores": {"test": 0.95},
            "processing_time_ms": 10,  # Fast mock time
        }

        return mock_service

    @staticmethod
    def mock_async_pdf_service():
        """Mock async PDF service with optimized responses."""
        mock_service = AsyncMock()

        # Mock async operations with minimal delay
        async def fast_validate_pdf_file(*args, **kwargs):
            await asyncio.sleep(0.001)  # Minimal delay for realism
            return True

        async def fast_extract_metadata(*args, **kwargs):
            await asyncio.sleep(0.001)
            return {
                "page_count": 1,
                "file_size": 1024,
                "encrypted": False,
                "creation_date": "2024-01-01T12:00:00Z",
                "modification_date": "2024-01-01T12:00:00Z",
            }

        async def fast_render_page(*args, **kwargs):
            await asyncio.sleep(0.001)
            return b"\x89PNG\r\n\x1a\n" + b"mock_png_data"

        async def fast_analyze_document(*args, **kwargs):
            await asyncio.sleep(0.001)
            return {
                "document_id": str(uuid.uuid4()),
                "total_pages": 1,
                "extracted_fields": {"test": "data"},
                "confidence_scores": {"test": 0.95},
                "processing_time_ms": 1,  # Fast mock time
            }

        mock_service.validate_pdf_file = fast_validate_pdf_file
        mock_service.extract_metadata = fast_extract_metadata
        mock_service.render_page = fast_render_page
        mock_service.analyze_document = fast_analyze_document

        return mock_service

    @staticmethod
    def mock_file_operations():
        """Mock file system operations for speed."""
        mock_ops = Mock()

        # Mock file saving (no actual I/O)
        mock_ops.save_file.return_value = Path("/mock/path/file.pdf")

        # Mock file reading (return minimal PDF content)
        mock_ops.read_file.return_value = b"%PDF-1.4\n%%EOF"

        # Mock file deletion (no actual I/O)
        mock_ops.delete_file.return_value = True

        # Mock file existence checks
        mock_ops.file_exists.return_value = True

        return mock_ops


class MockResponseFactory:
    """Factory for creating optimized mock responses."""

    @staticmethod
    def upload_success(
        file_id: Optional[str] = None, filename: str = "test.pdf", **overrides: Any
    ) -> Dict[str, Any]:
        """Create optimized upload success response."""
        return {
            "file_id": file_id or str(uuid.uuid4()),
            "filename": filename,
            "mime_type": "application/pdf",
            "file_size": 1024,
            "upload_timestamp": "2024-01-01T12:00:00Z",
            "metadata": {
                "page_count": 1,
                "file_size": 1024,
                "encrypted": False,
            },
            **overrides,
        }

    @staticmethod
    def analysis_success(
        document_id: Optional[str] = None, **overrides: Any
    ) -> Dict[str, Any]:
        """Create optimized analysis success response."""
        return {
            "document_id": document_id or str(uuid.uuid4()),
            "filename": "test.pdf",
            "total_pages": 1,
            "has_extractable_text": True,
            "file_size_mb": 0.001,  # Small for fast processing
            "extracted_fields": {"test": "data"},
            "confidence_scores": {"test": 0.95},
            "processing_time_ms": 1,  # Very fast
            **overrides,
        }

    @staticmethod
    def error_response(
        error_code: str = "TEST_ERROR",
        detail: str = "Test error message",
        **overrides: Any,
    ) -> Dict[str, Any]:
        """Create optimized error response."""
        return {
            "detail": detail,
            "error_code": error_code,
            "correlation_id": "test-correlation-id",
            **overrides,
        }


@pytest.fixture(scope="session")
def optimized_pdf_mocks():
    """Session-scoped optimized PDF mocks."""
    return OptimizedPDFMocks()


@pytest.fixture(scope="session")
def mock_response_factory():
    """Session-scoped mock response factory."""
    return MockResponseFactory()


@pytest.fixture(scope="session")
def fast_pdf_content():
    """Minimal PDF content for fast tests."""
    return b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
175
%%EOF"""


@pytest.fixture(scope="session")
def performance_config():
    """Configuration for performance-optimized tests."""
    return {
        "mock_delays": {
            "upload": 0.001,
            "analysis": 0.001,
            "render": 0.001,
            "metadata": 0.001,
        },
        "response_sizes": {
            "small_pdf": 1024,
            "medium_pdf": 10240,
            "large_pdf": 102400,
        },
        "timeouts": {
            "fast_test": 0.1,
            "normal_test": 1.0,
            "slow_test": 5.0,
        },
    }


def optimize_for_unit_tests(func):
    """Decorator to optimize functions for unit test performance."""

    def wrapper(*args, **kwargs):
        # Add performance optimizations
        kwargs.setdefault("timeout", 0.1)
        kwargs.setdefault("use_mocks", True)
        return func(*args, **kwargs)

    return wrapper


def skip_slow_operations(func):
    """Decorator to skip slow operations in unit tests."""

    def wrapper(*args, **kwargs):
        # Skip file I/O, network calls, etc. in unit tests
        if kwargs.get("test_type") == "unit":
            return Mock(return_value=True)
        return func(*args, **kwargs)

    return wrapper
