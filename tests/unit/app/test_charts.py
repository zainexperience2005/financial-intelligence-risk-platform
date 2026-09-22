from fastapi.testclient import TestClient

from app.analytics.charts import (
    build_category_chart,
    build_failed_transactions_chart,
    build_revenue_chart,
)
from app.analytics.operations import group_and_sum
from app.graphs.state import FinancialState
from app.main import app
from app.schemas.data_analysis import DataAnalysisResult
from app.services.evidence import build_evidence_bundle
from app.tools.charting import ChartInput, ChartTool
from kit.charts.models import ChartArtifact, ChartType


def test_build_revenue_chart_matches_rows():
    rows = [
        {"month": "2026-06", "revenue": 120000.0},
        {"month": "2026-07", "revenue": 145000.0},
        {"month": "2026-08", "revenue": 172000.0},
    ]

    spec = build_revenue_chart(rows)

    assert spec.chart_type == ChartType.LINE
    assert spec.filename == "revenue-over-time.png"
    assert len(spec.series) == 1
    assert spec.series[0].x == ["2026-06", "2026-07", "2026-08"]
    assert spec.series[0].y == [120000.0, 145000.0, 172000.0]


def test_build_failed_transactions_chart():
    rows = [
        {"month": "2026-01", "count": 12},
        {"month": "2026-02", "count": 19},
        {"month": "2026-03", "count": 8},
    ]

    spec = build_failed_transactions_chart(rows)

    assert spec.chart_type == ChartType.LINE
    assert spec.filename == "failed-transactions-trend.png"
    assert spec.series[0].x == ["2026-01", "2026-02", "2026-03"]
    assert spec.series[0].y == [12.0, 19.0, 8.0]


def test_build_category_chart():
    rows = [
        {"status": "completed", "count": 500},
        {"status": "failed", "count": 25},
    ]

    spec = build_category_chart(
        rows,
        category_column="status",
        value_column="count",
    )

    assert spec.chart_type == ChartType.BAR
    assert spec.series[0].x == ["completed", "failed"]
    assert spec.series[0].y == [500.0, 25.0]


def test_chart_tool_execution(tmp_path):
    rows = [
        {"month": "2026-01", "revenue": 5000.0},
        {"month": "2026-02", "revenue": 7500.0},
    ]
    spec = build_revenue_chart(rows)

    tool = ChartTool(output_dir=tmp_path)
    result = tool.execute(ChartInput(spec=spec))

    assert result.success is True
    assert result.data is not None
    assert result.data["filename"] == "revenue-over-time.png"
    assert result.data["chart_type"] == "line"
    assert result.data["data_points"] == 2
    assert (tmp_path / "revenue-over-time.png").exists()


def test_chart_metadata_in_evidence_bundle(tmp_path):
    artifact = ChartArtifact(
        filename="revenue-over-time.png",
        path=str(tmp_path / "revenue-over-time.png"),
        chart_type=ChartType.LINE,
        title="Revenue Over Time",
        data_points=3,
        truncated=False,
    )

    analysis_result = DataAnalysisResult(
        summary="Revenue trend shows positive growth.",
        operation="group_sum",
        result=[{"month": "2026-06", "revenue": 120000}],
        source_row_count=1,
        chart=artifact,
    )

    state: FinancialState = {
        "question": "Show revenue over time",
        "data_analysis": analysis_result,
    }  # type: ignore[typeddict-item]

    bundle = build_evidence_bundle(state)

    assert "chart" in bundle
    assert bundle["chart"]["filename"] == "revenue-over-time.png"
    assert bundle["chart"]["data_points"] == 3
    assert bundle["chart"]["chart_type"] == ChartType.LINE
    # Ensure binary content / internal paths are not exposed in evidence bundle
    assert "path" not in bundle["chart"]


def test_end_to_end_analytics_and_chart_exact_values(tmp_path):
    # Simulates:
    # 1. SQL rows retrieved
    # 2. Deterministic analytics (group_and_sum)
    # 3. Deterministic chart builder
    # 4. Renderer execution
    # 5. Verifies: chart values == deterministically calculated values
    raw_sql_rows = [
        {"month": "2026-01", "amount": 100.0},
        {"month": "2026-01", "amount": 200.0},
        {"month": "2026-02", "amount": 400.0},
        {"month": "2026-02", "amount": 100.0},
    ]

    analytics_result = group_and_sum(
        raw_sql_rows,
        group_by="month",
        value_column="amount",
    )
    # Sorted descending by amount: 2026-02 -> 500.0, 2026-01 -> 300.0
    sorted_by_month = sorted(
        analytics_result,
        key=lambda r: r["month"],
    )

    spec = build_revenue_chart(
        [{"month": r["month"], "revenue": r["amount"]} for r in sorted_by_month]
    )

    tool = ChartTool(output_dir=tmp_path)
    tool_result = tool.execute(ChartInput(spec=spec))

    assert tool_result.success is True

    # Critical requirement: Chart series values EQUAL analytics values exactly
    assert spec.series[0].x == ["2026-01", "2026-02"]
    assert spec.series[0].y == [300.0, 500.0]
    assert spec.series[0].y[0] == next(
        r["amount"] for r in analytics_result if r["month"] == "2026-01"
    )
    assert spec.series[0].y[1] == next(
        r["amount"] for r in analytics_result if r["month"] == "2026-02"
    )


def test_chart_endpoint_serves_valid_file(tmp_path, monkeypatch):
    from app.api.routes import charts

    test_file = tmp_path / "test-chart.png"
    test_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRfake")

    monkeypatch.setattr(
        charts,
        "CHART_OUTPUT_DIR",
        tmp_path,
    )

    client = TestClient(app)
    response = client.get("/api/v1/charts/test-chart.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRfake"
