"""Tests for the dependencies module."""

import pytest
from unittest.mock import Mock

from backend.app.dependencies import (
    get_pdf_service,
    init_pdf_service,
    reset_pdf_service,
    create_service_dependency,
)
from backend.app.services.pdf_service import PDFService


class TestPDFServiceDependency:
    """Test PDF service dependency injection."""

    def test_init_pdf_service(self):
        """Test initializing the PDF service."""
        # Reset state using public API
        reset_pdf_service()

        # Create and initialize service
        service = Mock(spec=PDFService)
        init_pdf_service(service)

        # Verify service was set by trying to get it
        result = get_pdf_service()
        assert result is service

    def test_get_pdf_service_with_initialized_service(self):
        """Test getting an initialized service."""
        # Reset state using public API
        reset_pdf_service()

        # Initialize with a mock service
        mock_service = Mock(spec=PDFService)
        init_pdf_service(mock_service)

        # Get the service
        result = get_pdf_service()

        # Should return the same instance
        assert result is mock_service

    def test_get_pdf_service_fallback_to_new_instance(self):
        """Test fallback to new instance when not initialized."""
        # Reset state using public API
        reset_pdf_service()

        # Get service without initialization
        result = get_pdf_service()

        # Should return a new PDFService instance
        assert isinstance(result, PDFService)

    def test_reset_pdf_service(self):
        """Test resetting the PDF service."""
        # Initialize with a mock service
        mock_service = Mock(spec=PDFService)
        init_pdf_service(mock_service)

        # Verify service is set
        assert get_pdf_service() is mock_service

        # Reset the service
        reset_pdf_service()

        # After reset, should get a new instance
        result = get_pdf_service()
        assert result is not mock_service
        assert isinstance(result, PDFService)

    def test_create_service_dependency(self):
        """Test creating a service dependency function."""
        # Reset state using public API
        reset_pdf_service()

        # Create a mock service
        mock_service = Mock(spec=PDFService)

        # Create dependency function
        def service_getter():
            return mock_service

        dependency_func = create_service_dependency(service_getter)

        # Call the dependency function
        result = dependency_func()

        # Should return the mock service
        assert result is mock_service

    def test_create_service_dependency_with_none(self):
        """Test dependency function fallback when service is None."""
        # Reset state using public API
        reset_pdf_service()

        # Create dependency function that returns None
        def service_getter():
            return None

        dependency_func = create_service_dependency(service_getter)

        # Call the dependency function
        result = dependency_func()

        # Should return a new PDFService instance
        assert isinstance(result, PDFService)
