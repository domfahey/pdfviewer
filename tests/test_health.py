from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test the health check endpoint."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "storage_available" in data

    assert data["version"] == "0.1.0"
    assert data["status"] in ["healthy", "degraded"]
    assert isinstance(data["storage_available"], bool)


def test_root_endpoint(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert data == {"message": "PDF Viewer API is running"}
