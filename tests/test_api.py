"""Integration tests for FastAPI application endpoints."""

from fastapi.testclient import TestClient


def test_health_check_structure(client: TestClient) -> None:
    """Test that the /health endpoint returns the expected JSON structure.

    If PostgreSQL is connected, returns 200 with status: healthy.
    If PostgreSQL is offline, returns 503 with status: unhealthy.
    Both cases confirm the healthcheck properly exercises app and database layers.
    """
    response = client.get("/health")
    assert response.status_code in (200, 503)
    data = response.json()
    if response.status_code == 200:
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["app"] == "portfolio-risk-analytics"
    else:
        assert data["detail"]["status"] == "unhealthy"
        assert data["detail"]["database"] == "disconnected"
        assert data["detail"]["app"] == "portfolio-risk-analytics"
