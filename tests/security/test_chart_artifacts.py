import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from kit.charts.models import (
    ChartSeries,
    ChartSpec,
    ChartType,
)


@pytest.mark.parametrize(
    "invalid_filename",
    [
        "../../secret.png",
        "../chart.png",
        "/tmp/chart.png",
        "charts/test.png",
        "nested/path/image.png",
        "evil.exe",
        "image.svg",
        "chart.jpg",
        "chart.png;rm -rf",
        "chart..png",
    ],
)
def test_path_traversal_filenames_rejected(invalid_filename: str):
    with pytest.raises(ValidationError):
        ChartSpec(
            chart_type=ChartType.LINE,
            title="Attempted Traversal",
            series=[
                ChartSeries(
                    name="Test",
                    x=["A"],
                    y=[1.0],
                )
            ],
            filename=invalid_filename,
        )


@pytest.mark.parametrize(
    "valid_filename",
    [
        "monthly-revenue.png",
        "revenue_2026.png",
        "trend-chart-1.png",
        "TransactionVolume.png",
    ],
)
def test_valid_filenames_accepted(valid_filename: str):
    spec = ChartSpec(
        chart_type=ChartType.LINE,
        title="Valid Filename",
        series=[
            ChartSeries(
                name="Test",
                x=["A"],
                y=[1.0],
            )
        ],
        filename=valid_filename,
    )
    assert spec.filename == valid_filename


def test_chart_endpoint_rejects_path_traversal():
    client = TestClient(app)

    # Path traversal patterns should fail validation or return not found / bad request
    response = client.get("/api/v1/charts/..%2Fsecret.png")
    assert response.status_code in (400, 404)

    response = client.get("/api/v1/charts/subfolder%2Fchart.png")
    assert response.status_code in (400, 404)


def test_chart_endpoint_returns_404_for_missing_file():
    client = TestClient(app)
    response = client.get("/api/v1/charts/nonexistent-chart.png")
    assert response.status_code == 404
    data = response.json()
    assert "Chart not found" in (data.get("message") or data.get("detail", ""))

