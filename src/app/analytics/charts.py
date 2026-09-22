from typing import Any

from kit.charts.models import (
    ChartSeries,
    ChartSpec,
    ChartType,
)


def build_revenue_chart(
    rows: list[dict[str, Any]],
) -> ChartSpec:
    """Builds a deterministic line chart spec for revenue over time."""
    return ChartSpec(

        chart_type=ChartType.LINE,
        title="Revenue Over Time",
        x_label="Period",
        y_label="Revenue",
        series=[
            ChartSeries(
                name="Revenue",
                x=[str(row["month"]) for row in rows],
                y=[float(row["revenue"]) for row in rows],
            )
        ],
        filename="revenue-over-time.png",
    )


def build_failed_transactions_chart(
    rows: list[dict[str, Any]],
) -> ChartSpec:
    """Builds a deterministic line chart spec for failed transactions trend."""
    x_vals: list[str] = []
    y_vals: list[float] = []

    for row in rows:
        x_val = str(
            row.get("month")
            or row.get("period")
            or row.get("date")
            or row.get("timestamp")
            or "unknown"
        )
        y_val = float(
            row.get("count")
            or row.get("failed_count")
            or row.get("failures")
            or row.get("failed_transactions")
            or row.get("value")
            or 0.0
        )
        x_vals.append(x_val)
        y_vals.append(y_val)

    return ChartSpec(
        chart_type=ChartType.LINE,
        title="Failed Transactions Trend",
        x_label="Period",
        y_label="Failed Transactions",
        series=[
            ChartSeries(
                name="Failed Transactions",
                x=x_vals,
                y=y_vals,
            )
        ],
        filename="failed-transactions-trend.png",
    )


def build_category_chart(
    rows: list[dict[str, Any]],
    category_column: str,
    value_column: str = "count",
    title: str = "Category Distribution",
    filename: str = "category-distribution.png",
) -> ChartSpec:
    """Builds a deterministic bar chart spec for categorical distributions."""
    return ChartSpec(
        chart_type=ChartType.BAR,
        title=title,
        x_label=category_column.capitalize(),
        y_label=value_column.capitalize(),
        series=[
            ChartSeries(
                name=category_column.capitalize(),
                x=[str(row[category_column]) for row in rows],
                y=[float(row[value_column]) for row in rows],
            )
        ],
        filename=filename,
    )
