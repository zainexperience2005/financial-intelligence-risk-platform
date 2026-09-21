from unittest.mock import AsyncMock, patch

import pytest

from app.api.schemas.investigations import InvestigationResponse
from app.core.exceptions import InvestigationError
from app.schemas.report import InvestigationReport


@pytest.mark.integration
def test_investigate_success(client):
    mock_response = InvestigationResponse(
        thread_id="test-thread-101",
        report=InvestigationReport(
            executive_summary="All checks normal.",
            recommendation="none",
            evidence_sufficient=True,
        ),
    )

    with patch(
        "app.services.investigation.InvestigationService.investigate",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = client.post(
            "/api/v1/investigations",
            json={
                "question": "Is account ACC-1001 suspicious?",
                "thread_id": "test-thread-101",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "test-thread-101"
        assert data["report"]["executive_summary"] == "All checks normal."
        assert "X-Request-ID" in response.headers


@pytest.mark.integration
def test_investigate_validation_failure(client):
    response = client.post(
        "/api/v1/investigations",
        json={
            "question": "",
            "thread_id": "test-thread-101",
        },
    )

    assert response.status_code == 422


@pytest.mark.integration
def test_investigate_domain_error_mapped(client):
    with patch(
        "app.services.investigation.InvestigationService.investigate",
        new_callable=AsyncMock,
        side_effect=InvestigationError("Investigation failed due to upstream timeout."),
    ):
        response = client.post(
            "/api/v1/investigations",
            json={
                "question": "Analyze transaction TX-999",
                "thread_id": "test-thread-err",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "investigation_failed"
        assert "upstream timeout" in data["message"]
        assert "request_id" in data
        assert "X-Request-ID" in response.headers
