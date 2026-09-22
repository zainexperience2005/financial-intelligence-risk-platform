import pytest

from kit.charts.matplotlib import (
    ChartValidationError,
    render_chart,
)
from kit.charts.models import (
    MAX_CHART_POINTS,
    MAX_CHART_SERIES,
    ChartSeries,
    ChartSpec,
    ChartType,
)


def test_line_chart_is_created(tmp_path):
    spec = ChartSpec(
        chart_type=ChartType.LINE,
        title="Revenue",
        x_label="Month",
        y_label="Revenue",
        series=[
            ChartSeries(
                name="Revenue",
                x=["Jan", "Feb", "Mar"],
                y=[100.0, 150.0, 125.0],
            )
        ],
        filename="revenue.png",
    )

    artifact = render_chart(
        spec=spec,
        output_dir=tmp_path,
    )

    assert (tmp_path / "revenue.png").exists()
    assert artifact.data_points == 3
    assert not artifact.truncated
    assert artifact.filename == "revenue.png"
    assert artifact.chart_type == ChartType.LINE


def test_bar_chart_is_created(tmp_path):
    spec = ChartSpec(
        chart_type=ChartType.BAR,
        title="Transaction Categories",
        x_label="Category",
        y_label="Count",
        series=[
            ChartSeries(
                name="Count",
                x=["Wire", "Card", "ACH"],
                y=[45.0, 120.0, 80.0],
            )
        ],
        filename="categories.png",
    )

    artifact = render_chart(
        spec=spec,
        output_dir=tmp_path,
    )

    assert (tmp_path / "categories.png").exists()
    assert artifact.data_points == 3
    assert not artifact.truncated
    assert artifact.chart_type == ChartType.BAR


def test_mismatched_xy_is_rejected(tmp_path):
    spec = ChartSpec(
        chart_type=ChartType.LINE,
        title="Invalid",
        series=[
            ChartSeries(
                name="Revenue",
                x=["Jan", "Feb"],
                y=[100.0],
            )
        ],
        filename="invalid.png",
    )

    with pytest.raises(ChartValidationError, match="equal lengths"):
        render_chart(
            spec=spec,
            output_dir=tmp_path,
        )


def test_no_series_is_rejected(tmp_path):
    spec = ChartSpec(
        chart_type=ChartType.LINE,
        title="Empty",
        series=[],
        filename="empty.png",
    )

    with pytest.raises(ChartValidationError, match="at least one series"):
        render_chart(
            spec=spec,
            output_dir=tmp_path,
        )


def test_max_series_exceeded_is_rejected(tmp_path):
    series_list = [
        ChartSeries(
            name=f"S{i}",
            x=["A"],
            y=[1.0],
        )
        for i in range(MAX_CHART_SERIES + 1)
    ]
    spec = ChartSpec(
        chart_type=ChartType.LINE,
        title="Too Many Series",
        series=series_list,
        filename="too-many.png",
    )

    with pytest.raises(ChartValidationError, match="Too many chart series"):
        render_chart(
            spec=spec,
            output_dir=tmp_path,
        )


def test_chart_points_truncation_limit(tmp_path):
    # 100 points should be truncated to MAX_CHART_POINTS (50)
    spec = ChartSpec(
        chart_type=ChartType.LINE,
        title="High Volume",
        series=[
            ChartSeries(
                name="Volume",
                x=[f"p_{i}" for i in range(100)],
                y=[float(i) for i in range(100)],
            )
        ],
        filename="high-volume.png",
    )

    artifact = render_chart(
        spec=spec,
        output_dir=tmp_path,
    )

    assert (tmp_path / "high-volume.png").exists()
    assert artifact.data_points == MAX_CHART_POINTS
    assert artifact.truncated is True
