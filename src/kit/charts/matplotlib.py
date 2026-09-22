from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from kit.charts.models import (
    MAX_CHART_POINTS,
    MAX_CHART_SERIES,
    ChartArtifact,
    ChartSpec,
    ChartType,
)


class ChartValidationError(ValueError):
    pass


def render_chart(
    *,
    spec: ChartSpec,
    output_dir: Path,
) -> ChartArtifact:
    if not spec.series:
        raise ChartValidationError("Chart requires at least one series.")

    if len(spec.series) > MAX_CHART_SERIES:
        raise ChartValidationError("Too many chart series.")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots()

    total_points = 0
    truncated = False

    try:
        for series in spec.series:
            if len(series.x) != len(series.y):
                raise ChartValidationError("X and Y values must have equal lengths.")

            x = series.x[:MAX_CHART_POINTS]
            y = series.y[:MAX_CHART_POINTS]

            if len(series.x) > MAX_CHART_POINTS:
                truncated = True

            total_points += len(x)

            if spec.chart_type == ChartType.BAR:
                ax.bar(
                    x,
                    y,
                    label=series.name,
                )
            elif spec.chart_type == ChartType.LINE:
                ax.plot(
                    x,
                    y,
                    marker="o",
                    label=series.name,
                )
            else:
                raise ChartValidationError(f"Unsupported chart type: {spec.chart_type}")

        ax.set_title(spec.title)

        if spec.x_label:
            ax.set_xlabel(spec.x_label)

        if spec.y_label:
            ax.set_ylabel(spec.y_label)

        if len(spec.series) > 1:
            ax.legend()

        fig.tight_layout()

        path = output_dir / spec.filename
        fig.savefig(path)

        return ChartArtifact(
            filename=spec.filename,
            path=str(path),
            chart_type=spec.chart_type,
            title=spec.title,
            data_points=total_points,
            truncated=truncated,
        )
    finally:
        plt.close(fig)
