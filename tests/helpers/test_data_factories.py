"""
Test data factories for creating complex test scenarios.

This module provides factories for creating test data with specific variations
and characteristics, supporting parameterized testing and edge case coverage.
"""

from datetime import datetime
from typing import Dict, Any, List
from tests.config import TestConstants


class PDFDataFactory:
    """Factory for creating PDF-related test data with various characteristics."""

    @staticmethod
    def create_upload_scenario(
        document_type: str = "standard",
        file_size_category: str = "medium",
        success_expected: bool = True,
        **overrides: Any,
    ) -> Dict[str, Any]:
        """
        Create a complete upload test scenario.

        Args:
            document_type: Type of document (standard, government, image_rich, scanned)
            file_size_category: Size category (small, medium, large, oversized)
            success_expected: Whether upload should succeed
            **overrides: Additional parameters to override defaults

        Returns:
            Dict containing scenario configuration
        """
        base_config = TestConstants.REAL_PDF_SAMPLES.get(
            f"{document_type}_sample",
            TestConstants.REAL_PDF_SAMPLES["integration_sample"],
        )

        # File size mappings
        size_mapping = {
            "small": TestConstants.SMALL_FILE_SIZE,
            "medium": TestConstants.MEDIUM_FILE_SIZE,
            "large": TestConstants.MEDIUM_FILE_SIZE * 10,
            "oversized": TestConstants.LARGE_FILE_SIZE,
        }

        expected_status = (
            200 if success_expected and file_size_category != "oversized" else 413
        )

        scenario = {
            "document_type": document_type,
            "filename": f"test_{document_type}_{file_size_category}.pdf",
            "expected_file_size": size_mapping.get(
                file_size_category, TestConstants.MEDIUM_FILE_SIZE
            ),
            "expected_status_code": expected_status,
            "expected_pages": base_config.get("expected_pages", 1),
            "has_extractable_text": base_config.get("has_extractable_text", True),
            "encrypted": base_config.get("encrypted", False),
            "performance_category": base_config.get("performance_category", "fast"),
            "mime_type": "application/pdf",
            "upload_timeout": TestConstants.DEFAULT_UPLOAD_TIMEOUT,
            **overrides,
        }

        return scenario

    @staticmethod
    def create_metadata_scenario(
        complexity: str = "simple", **overrides: Any
    ) -> Dict[str, Any]:
        """
        Create metadata extraction test scenario.

        Args:
            complexity: Complexity level (simple, medium, complex)
            **overrides: Additional parameters to override defaults

        Returns:
            Dict containing metadata scenario configuration
        """
        complexity_configs = {
            "simple": {
                "page_count": 1,
                "has_images": False,
                "has_forms": False,
                "text_density": "high",
                "processing_time_category": "fast",
            },
            "medium": {
                "page_count": 5,
                "has_images": True,
                "has_forms": False,
                "text_density": "medium",
                "processing_time_category": "medium",
            },
            "complex": {
                "page_count": 52,
                "has_images": True,
                "has_forms": True,
                "text_density": "low",
                "processing_time_category": "slow",
            },
        }

        base_config = complexity_configs.get(complexity, complexity_configs["simple"])

        scenario = {
            "complexity": complexity,
            "expected_metadata": {
                "page_count": base_config["page_count"],
                "file_size": TestConstants.MEDIUM_FILE_SIZE,
                "encrypted": False,
                "creation_date": datetime.now().isoformat(),
                "modification_date": datetime.now().isoformat(),
            },
            "processing_characteristics": {
                "has_images": base_config["has_images"],
                "has_forms": base_config["has_forms"],
                "text_density": base_config["text_density"],
                "processing_time_category": base_config["processing_time_category"],
            },
            "performance_thresholds": {
                "max_processing_time": TestConstants.PERFORMANCE_THRESHOLDS.get(
                    f"metadata_extraction_{base_config['processing_time_category']}",
                    30.0,
                )
            },
            **overrides,
        }

        return scenario


class ErrorScenarioFactory:
    """Factory for creating error test scenarios."""

    @staticmethod
    def create_validation_error_scenario(
        error_type: str = "invalid_file_type", **overrides: Any
    ) -> Dict[str, Any]:
        """
        Create validation error test scenario.

        Args:
            error_type: Type of validation error
            **overrides: Additional parameters to override defaults

        Returns:
            Dict containing error scenario configuration
        """
        error_configs = {
            "invalid_file_type": {
                "filename": "test.txt",
                "content_type": "text/plain",
                "expected_status": 400,
                "expected_error_code": "INVALID_FILE_TYPE",
                "expected_message": "Only PDF files are allowed",
            },
            "oversized_file": {
                "filename": "huge.pdf",
                "content_type": "application/pdf",
                "file_size": TestConstants.LARGE_FILE_SIZE,
                "expected_status": 413,
                "expected_error_code": "FILE_TOO_LARGE",
                "expected_message": "File too large",
            },
            "empty_file": {
                "filename": "empty.pdf",
                "content_type": "application/pdf",
                "file_size": 0,
                "expected_status": 400,
                "expected_error_code": "EMPTY_FILE",
                "expected_message": "Empty file not allowed",
            },
            "corrupted_pdf": {
                "filename": "corrupted.pdf",
                "content_type": "application/pdf",
                "content": b"not a real pdf",
                "expected_status": 400,
                "expected_error_code": "INVALID_PDF",
                "expected_message": "Invalid PDF file",
            },
        }

        base_config = error_configs.get(error_type, error_configs["invalid_file_type"])

        scenario = {
            "error_type": error_type,
            "test_file": {
                "filename": base_config["filename"],
                "content_type": base_config["content_type"],
                "file_size": base_config.get("file_size"),
                "content": base_config.get("content"),
            },
            "expected_response": {
                "status_code": base_config["expected_status"],
                "error_code": base_config["expected_error_code"],
                "message_contains": base_config["expected_message"],
            },
            **overrides,
        }

        return scenario


class PerformanceScenarioFactory:
    """Factory for creating performance test scenarios."""

    @staticmethod
    def create_load_test_scenario(
        load_type: str = "normal", **overrides: Any
    ) -> Dict[str, Any]:
        """
        Create load testing scenario.

        Args:
            load_type: Type of load test (light, normal, heavy, stress)
            **overrides: Additional parameters to override defaults

        Returns:
            Dict containing load test scenario configuration
        """
        load_configs = {
            "light": {
                "concurrent_users": 2,
                "requests_per_user": 5,
                "ramp_up_time": 5,
                "max_response_time": 2.0,
                "success_rate_threshold": 99.0,
            },
            "normal": {
                "concurrent_users": 5,
                "requests_per_user": 10,
                "ramp_up_time": 10,
                "max_response_time": 5.0,
                "success_rate_threshold": 95.0,
            },
            "heavy": {
                "concurrent_users": 10,
                "requests_per_user": 20,
                "ramp_up_time": 20,
                "max_response_time": 10.0,
                "success_rate_threshold": 90.0,
            },
            "stress": {
                "concurrent_users": 20,
                "requests_per_user": 50,
                "ramp_up_time": 30,
                "max_response_time": 30.0,
                "success_rate_threshold": 80.0,
            },
        }

        base_config = load_configs.get(load_type, load_configs["normal"])

        scenario = {
            "load_type": load_type,
            "load_parameters": base_config,
            "test_data": {
                "file_size_distribution": {
                    "small": 30,  # 30% small files
                    "medium": 60,  # 60% medium files
                    "large": 10,  # 10% large files
                },
                "document_type_distribution": {
                    "standard": 50,
                    "government": 25,
                    "image_rich": 15,
                    "scanned": 10,
                },
            },
            "monitoring": {
                "track_response_times": True,
                "track_error_rates": True,
                "track_resource_usage": True,
                "alert_thresholds": {
                    "response_time_p95": base_config["max_response_time"],
                    "error_rate": 100 - base_config["success_rate_threshold"],
                },
            },
            **overrides,
        }

        return scenario


class APITestScenarioFactory:
    """Factory for creating API test scenarios."""

    @staticmethod
    def create_endpoint_test_matrix(
        endpoint: str = "upload", **overrides: Any
    ) -> List[Dict[str, Any]]:
        """
        Create comprehensive test matrix for an API endpoint.

        Args:
            endpoint: API endpoint to test (upload, metadata, delete)
            **overrides: Additional parameters to override defaults

        Returns:
            List of test scenario configurations
        """
        if endpoint == "upload":
            return [
                # Success scenarios
                PDFDataFactory.create_upload_scenario("standard", "small", True),
                PDFDataFactory.create_upload_scenario("standard", "medium", True),
                PDFDataFactory.create_upload_scenario("government", "medium", True),
                PDFDataFactory.create_upload_scenario("image_rich", "large", True),
                # Error scenarios
                ErrorScenarioFactory.create_validation_error_scenario(
                    "invalid_file_type"
                ),
                ErrorScenarioFactory.create_validation_error_scenario("oversized_file"),
                ErrorScenarioFactory.create_validation_error_scenario("empty_file"),
                ErrorScenarioFactory.create_validation_error_scenario("corrupted_pdf"),
            ]
        elif endpoint == "metadata":
            return [
                PDFDataFactory.create_metadata_scenario("simple"),
                PDFDataFactory.create_metadata_scenario("medium"),
                PDFDataFactory.create_metadata_scenario("complex"),
            ]
        else:
            return []

    @staticmethod
    def create_integration_test_flow(
        flow_type: str = "happy_path", **overrides: Any
    ) -> Dict[str, Any]:
        """
        Create integration test flow scenario.

        Args:
            flow_type: Type of integration flow (happy_path, error_recovery, edge_case)
            **overrides: Additional parameters to override defaults

        Returns:
            Dict containing integration flow configuration
        """
        flows = {
            "happy_path": {
                "name": "Complete PDF Processing Happy Path",
                "steps": [
                    {"action": "upload", "expected_status": 200},
                    {"action": "get_metadata", "expected_status": 200},
                    {"action": "get_pdf", "expected_status": 200},
                    {"action": "delete", "expected_status": 200},
                ],
                "cleanup_required": False,
            },
            "error_recovery": {
                "name": "Error Recovery Flow",
                "steps": [
                    {"action": "upload_invalid", "expected_status": 400},
                    {"action": "upload_valid", "expected_status": 200},
                    {"action": "get_metadata", "expected_status": 200},
                    {"action": "delete", "expected_status": 200},
                ],
                "cleanup_required": True,
            },
            "edge_case": {
                "name": "Edge Case Handling",
                "steps": [
                    {"action": "upload", "expected_status": 200},
                    {"action": "get_nonexistent_metadata", "expected_status": 404},
                    {"action": "get_metadata", "expected_status": 200},
                    {"action": "delete_twice", "expected_status": [200, 404]},
                ],
                "cleanup_required": True,
            },
        }

        base_flow = flows.get(flow_type, flows["happy_path"])

        scenario = {
            "flow_type": flow_type,
            "flow_config": base_flow,
            "test_data": PDFDataFactory.create_upload_scenario(),
            "validation": {
                "check_response_structure": True,
                "check_correlation_ids": True,
                "check_timing": True,
                "check_cleanup": base_flow["cleanup_required"],
            },
            **overrides,
        }

        return scenario


# Convenience functions for common test patterns
def get_standard_pdf_variations() -> List[Dict[str, Any]]:
    """Get standard PDF variations for parameterized tests."""
    return [
        PDFDataFactory.create_upload_scenario("standard", "small"),
        PDFDataFactory.create_upload_scenario("government", "medium"),
        PDFDataFactory.create_upload_scenario("image_rich", "large"),
        PDFDataFactory.create_upload_scenario("scanned", "medium"),
    ]


def get_error_test_cases() -> List[Dict[str, Any]]:
    """Get standard error test cases."""
    return [
        ErrorScenarioFactory.create_validation_error_scenario("invalid_file_type"),
        ErrorScenarioFactory.create_validation_error_scenario("oversized_file"),
        ErrorScenarioFactory.create_validation_error_scenario("empty_file"),
        ErrorScenarioFactory.create_validation_error_scenario("corrupted_pdf"),
    ]


def get_performance_test_scenarios() -> List[Dict[str, Any]]:
    """Get performance test scenarios."""
    return [
        PerformanceScenarioFactory.create_load_test_scenario("light"),
        PerformanceScenarioFactory.create_load_test_scenario("normal"),
        PerformanceScenarioFactory.create_load_test_scenario("heavy"),
    ]
