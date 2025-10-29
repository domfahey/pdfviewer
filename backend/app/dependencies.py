"""Shared FastAPI dependencies for the application."""

from typing import Callable

from .services.pdf_service import PDFService

# Global service instance variable
_pdf_service: PDFService | None = None


def init_pdf_service(service: PDFService) -> None:
    """Initialize the global PDF service instance.
    
    Args:
        service: The PDFService instance to use globally
    """
    global _pdf_service
    _pdf_service = service


def reset_pdf_service() -> None:
    """Reset the global PDF service instance.
    
    This is primarily used for testing to ensure clean state between tests.
    """
    global _pdf_service
    _pdf_service = None


def get_pdf_service() -> PDFService:
    """FastAPI dependency to get the PDF service instance.
    
    Returns:
        PDFService: The global service instance, or a new instance if not initialized
    """
    if _pdf_service is None:
        # Fallback to creating new instance if not initialized
        return PDFService()
    return _pdf_service


def create_service_dependency(
    service_getter: Callable[[], PDFService | None],
) -> Callable[[], PDFService]:
    """Create a dependency function for a service.
    
    This is a factory function for creating service dependencies with
    consistent fallback behavior.
    
    Args:
        service_getter: Function that returns the service or None
        
    Returns:
        Dependency function compatible with FastAPI Depends()
    """

    def dependency() -> PDFService:
        service = service_getter()
        if service is None:
            return PDFService()
        return service

    return dependency
