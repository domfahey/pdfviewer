from datetime import datetime

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test the health check endpoint."""
    response = client.get("/api/health")

    assert response.status_code == 200, "Health check should return 200 OK"
    data = response.json()

    assert "status" in data, "Health check response should include status field"
    assert "timestamp" in data, "Health check response should include timestamp field"
    assert "version" in data, "Health check response should include version field"
    assert (
        "storage_available" in data
    ), "Health check response should include storage_available field"

    assert data["version"] == "0.1.0", "Version should be 0.1.0"
    assert data["status"] in [
        "healthy",
        "degraded",
        "unhealthy",
    ], f"Status should be valid: {data['status']}"
    assert isinstance(
        data["storage_available"], bool
    ), "storage_available should be a boolean"

    # Check Pydantic v2 enhanced health response
    assert "is_healthy" in data, "Health check response should include is_healthy field"
    assert isinstance(data["is_healthy"], bool), "is_healthy should be a boolean"

    # Verify timestamp format
    assert "timestamp" in data
    timestamp_str = data["timestamp"]
    # Should be valid ISO format
    datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))


def test_root_endpoint(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/")

    assert response.status_code == 200, "Root endpoint should return 200 OK"
    data = response.json()

    assert data == {
        "message": "PDF Viewer API is running"
    }, "Root endpoint should return welcome message"


def test_health_check_correlation_id(client: TestClient):
    """Test health check includes correlation ID in response."""
    correlation_id = "health-test-123"

    response = client.get("/api/health", headers={"X-Correlation-ID": correlation_id})

    assert response.status_code == 200
    assert (
        response.headers.get("x-correlation-id") == correlation_id
    ), "Response should include the same correlation ID from request"



