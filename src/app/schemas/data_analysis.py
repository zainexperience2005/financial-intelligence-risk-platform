from typing import Any

from pydantic import BaseModel, Field

from kit.charts.models import ChartArtifact


class DataAnalysisResult(BaseModel):
    summary: str

    operation: str | None = None

    result: Any | None = None

    source_row_count: int = Field(
        default=0,
        ge=0,
    )

    chart: ChartArtifact | None = None
