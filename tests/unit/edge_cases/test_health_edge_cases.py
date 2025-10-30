"""Edge case tests for health check endpoint.

This module contains edge case tests for the health endpoint including:
- Status field validation edge cases
- Version format validation
- Storage availability edge cases
"""

import re

from fastapi.testclient import TestClient


def test_health_check_storage_availability_edge_case(client: TestClient):
    """Test health check when storage is unavailable."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    # Storage available should be boolean
    assert isinstance(
        data["storage_available"], bool
    ), "storage_available should be a boolean value"

    # If storage is not available, status should not be healthy
    if not data["storage_available"]:
        assert (
            data["status"] != "healthy"
        ), "Status should not be 'healthy' when storage is unavailable"


def test_health_check_version_format(client: TestClient):
    """Test health check version follows semantic versioning."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    version = data["version"]
    # Should match semantic versioning pattern (X.Y.Z)
    pattern = r"^\d+\.\d+\.\d+$"
    assert re.match(
        pattern, version
    ), f"Version '{version}' doesn't follow semantic versioning (X.Y.Z)"


def test_health_check_status_validation_edge_cases(client: TestClient):
    """Test health check status field validation with edge cases."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    # Status should be one of the valid values
    valid_statuses = ["healthy", "degraded", "unhealthy"]
    assert (
        data["status"] in valid_statuses
    ), f"Status '{data['status']}' should be one of {valid_statuses}"

    # is_healthy should match status
    if data["status"] == "healthy":
        assert (
            data["is_healthy"] is True
        ), "is_healthy should be True when status is 'healthy'"
    else:
        assert (
            data["is_healthy"] is False
        ), f"is_healthy should be False when status is '{data['status']}'"
