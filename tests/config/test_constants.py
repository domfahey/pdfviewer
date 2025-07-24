"""
Test constants and configuration for the PDF viewer test suite.

This module centralizes all test-related constants, file paths, and configuration
values to improve maintainability and consistency across the test suite.
"""

from pathlib import Path

# Base directory paths
TESTS_DIR = Path(__file__).parent.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
INTEGRATION_FIXTURES_DIR = TESTS_DIR / "integration" / "fixtures"
E2E_FIXTURES_DIR = TESTS_DIR / "e2e" / "fixtures"


class TestConstants:
    """Central configuration constants for tests."""

    # File size limits and test values
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    LARGE_FILE_SIZE = 51 * 1024 * 1024  # 51MB (exceeds limit)
    SMALL_FILE_SIZE = 1024  # 1KB
    MEDIUM_FILE_SIZE = 1024 * 1024  # 1MB

    # PDF characteristics
    DEFAULT_PAGES = 1
    MULTI_PAGE_COUNT = 5
    LARGE_PAGE_COUNT = 100

    # Mock response defaults
    DEFAULT_CONFIDENCE_SCORE = 0.95
    DEFAULT_PROCESSING_TIME_MS = 1250
    DEFAULT_UPLOAD_TIMEOUT = 30

    # Test client configuration
    DEFAULT_BASE_URL = "http://testserver"
    DEFAULT_TIMEOUT = 30.0

    # Directory paths
    FIXTURES_DIR = FIXTURES_DIR
    INTEGRATION_FIXTURES_DIR = INTEGRATION_FIXTURES_DIR
    E2E_FIXTURES_DIR = E2E_FIXTURES_DIR

    # Test PDF sample configurations
    PDF_SAMPLES = {
        "simple": {
            "description": "Minimal valid PDF for basic testing",
            "expected_pages": 1,
            "expected_size_range": (100, 1000),
            "has_text": True,
            "has_images": False,
            "encrypted": False,
        },
        "multi_page": {
            "description": "Multi-page PDF for pagination testing",
            "expected_pages": 5,
            "expected_size_range": (500, 5000),
            "has_text": True,
            "has_images": False,
            "encrypted": False,
        },
    }

    # Real PDF sample file configurations
    REAL_PDF_SAMPLES = {
        "epa_sample": {
            "filename": "epa_sample.pdf",
            "fallback_filename": None,
            "description": "EPA government document sample",
            "document_type": "government_document",
            "expected_pages": 1,
            "min_size": 1000,
            "has_extractable_text": True,
            "encrypted": False,
            "performance_category": "fast",  # <30s processing
        },
        "anyline_sample": {
            "filename": "anyline_book.pdf",
            "fallback_filename": "anyline_sample.pdf",
            "description": "Anyline image-rich document sample",
            "document_type": "image_rich_document",
            "expected_pages": 52,
            "min_size": 1000,
            "has_extractable_text": True,
            "encrypted": False,
            "performance_category": "slow",  # >30s processing
        },
        "integration_sample": {
            "filename": "sample.pdf",
            "fallback_filename": None,
            "description": "Standard integration test sample",
            "document_type": "standard_document",
            "expected_pages": 1,
            "min_size": 500,
            "has_extractable_text": True,
            "encrypted": False,
            "performance_category": "fast",
        },
        "image_based": {
            "filename": "image_based.pdf",
            "fallback_filename": None,
            "description": "Scanned/image-based PDF sample",
            "document_type": "scanned_document",
            "expected_pages": 1,
            "min_size": 1000,
            "has_extractable_text": False,
            "encrypted": False,
            "performance_category": "medium",  # 10-30s processing
        },
    }

    # Mock response templates
    MOCK_RESPONSE_TEMPLATES = {
        "upload_success": {
            "file_id": "550e8400-e29b-41d4-a716-446655440000",
            "filename": "test.pdf",
            "mime_type": "application/pdf",
            "file_size": 1048576,
            "upload_timestamp": "2024-01-01T12:00:00Z",
            "metadata": {"page_count": 1, "file_size": 1048576, "encrypted": False},
        },
        "upload_error": {
            "detail": "Only PDF files are allowed",
            "error_code": "INVALID_FILE_TYPE",
            "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
        },
        "metadata_success": {
            "page_count": 1,
            "file_size": 1048576,
            "encrypted": False,
            "creation_date": "2024-01-01T12:00:00Z",
            "modification_date": "2024-01-01T12:00:00Z",
        },
        "error_404": {
            "detail": "File not found",
            "error_code": "FILE_NOT_FOUND",
            "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
        },
    }

    # Performance test thresholds
    PERFORMANCE_THRESHOLDS = {
        "upload_time_fast": 5.0,  # seconds
        "upload_time_medium": 30.0,  # seconds
        "upload_time_slow": 60.0,  # seconds
        "metadata_extraction_fast": 2.0,  # seconds
        "api_response_fast": 1.0,  # seconds
    }

    # Test environment settings
    TEST_ENV_SETTINGS = {
        "cors_origins": [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
        ],
        "debug_mode": True,
        "log_level": "DEBUG",
        "upload_dir": "uploads",
        "temp_dir": "/tmp/pdfviewer_tests",
    }


# Legacy compatibility - maintain existing fixture names
LEGACY_FIXTURE_MAPPING = {
    "epa_sample_pdf_content": "epa_sample",
    "anyline_sample_pdf_content": "anyline_sample",
    "integration_sample_pdf_content": "integration_sample",
    "image_based_pdf_content": "image_based",
    "weblite_sample_pdf_content": "integration_sample",  # fallback mapping
    "princexml_sample_pdf_content": "anyline_sample",  # fallback mapping
    "nhtsa_form_pdf_content": "epa_sample",  # fallback mapping
}
