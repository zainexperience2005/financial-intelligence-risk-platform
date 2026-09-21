from unittest.mock import patch

import pytest


@pytest.mark.integration
def test_health(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "X-Request-ID" in response.headers


@pytest.mark.integration
def test_readiness_healthy(client):
    response = client.get("/api/v1/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "ok"
    assert "X-Request-ID" in response.headers


@pytest.mark.integration
def test_readiness_unhealthy(client):
    with patch(
        "app.api.routes.health.SessionFactory",
        side_effect=Exception("DB Down"),
    ):
        response = client.get("/api/v1/ready")

        assert response.status_code == 503
        data = response.json()
        assert data["error"] == "http_error"
        assert data["message"] == "Service not ready."
        assert "X-Request-ID" in response.headers


@pytest.mark.integration
def test_custom_request_id_preserved(client):
    custom_id = "req-custom-trace-12345"
    response = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": custom_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id
