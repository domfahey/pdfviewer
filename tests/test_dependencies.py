"""Tests for the dependencies module."""

import pytest
from unittest.mock import Mock

from backend.app.dependencies import (
    get_pdf_service,
    init_pdf_service,
    create_service_dependency,
    _pdf_service,
)
from backend.app.services.pdf_service import PDFService


class TestPDFServiceDependency:
    """Test PDF service dependency injection."""

    def test_init_pdf_service(self):
        """Test initializing the PDF service."""
        from backend.app import dependencies

        # Reset state
        dependencies._pdf_service = None

        # Create and initialize service
        service = Mock(spec=PDFService)
        init_pdf_service(service)

        # Verify service was set
        assert dependencies._pdf_service is service

    def test_get_pdf_service_with_initialized_service(self):
        """Test getting an initialized service."""
        from backend.app import dependencies

        # Reset state
        dependencies._pdf_service = None

        # Initialize with a mock service
        mock_service = Mock(spec=PDFService)
        init_pdf_service(mock_service)

        # Get the service
        result = get_pdf_service()

        # Should return the same instance
        assert result is mock_service

    def test_get_pdf_service_fallback_to_new_instance(self):
        """Test fallback to new instance when not initialized."""
        from backend.app import dependencies

        # Reset state
        dependencies._pdf_service = None

        # Get service without initialization
        result = get_pdf_service()

        # Should return a new PDFService instance
        assert isinstance(result, PDFService)
        assert result is not dependencies._pdf_service

    def test_create_service_dependency(self):
        """Test creating a service dependency function."""
        from backend.app import dependencies

        # Reset state
        dependencies._pdf_service = None

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
        from backend.app import dependencies

        # Reset state
        dependencies._pdf_service = None

        # Create dependency function that returns None
        def service_getter():
            return None

        dependency_func = create_service_dependency(service_getter)

        # Call the dependency function
        result = dependency_func()

        # Should return a new PDFService instance
        assert isinstance(result, PDFService)
