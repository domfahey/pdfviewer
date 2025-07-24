from fastapi.testclient import TestClient

from tests.helpers import assert_correlation_id_propagated, assert_timestamp_fields


def test_health_check(client: TestClient):
    """Test the health check endpoint."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    # Required health check fields
    required_fields = ["status", "timestamp", "version", "storage_available"]
    for field in required_fields:
        assert (
            field in data
        ), f"Missing required field '{field}' in health check response"

    # Validate field values
    assert data["version"] == "0.1.0"
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert isinstance(data["storage_available"], bool)

    # Check Pydantic v2 enhanced health response
    assert "is_healthy" in data
    assert isinstance(data["is_healthy"], bool)

    # Verify timestamp format using helper
    assert_timestamp_fields(data, "timestamp")


def test_root_endpoint(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert data == {"message": "PDF Viewer API is running"}


def test_health_check_correlation_id(client: TestClient):
    """Test health check includes correlation ID in response."""
    correlation_id = "health-test-123"

    response = client.get("/api/health", headers={"X-Correlation-ID": correlation_id})

    assert response.status_code == 200
    # Use helper to validate correlation ID propagation
    assert_correlation_id_propagated(response, correlation_id)


def test_health_check_status_validation(client: TestClient):
    """Test health check status field validation."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    # Status should be one of the valid values
    valid_statuses = ["healthy", "degraded", "unhealthy"]
    assert data["status"] in valid_statuses

    # is_healthy should match status
    if data["status"] == "healthy":
        assert data["is_healthy"] is True
    else:
        assert data["is_healthy"] is False


def test_health_check_version_format(client: TestClient):
    """Test health check version follows semantic versioning."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    version = data["version"]
    # Should match semantic versioning pattern (X.Y.Z)
    import re

    pattern = r"^\d+\.\d+\.\d+$"
    assert re.match(
        pattern, version
    ), f"Version {version} doesn't follow semantic versioning"


def test_health_check_storage_availability(client: TestClient):
    """Test health check storage availability checking."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    # Storage available should be boolean
    assert isinstance(data["storage_available"], bool)

    # If storage is not available, status should not be healthy
    if not data["storage_available"]:
        assert data["status"] != "healthy"
