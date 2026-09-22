from enum import StrEnum

from pydantic import BaseModel, Field

MAX_CHART_POINTS = 50
MAX_CHART_SERIES = 5
SAFE_FILENAME_REGEX = r"^[a-zA-Z0-9_-]+\.png$"


class ChartType(StrEnum):
    BAR = "bar"
    LINE = "line"


class ChartSeries(BaseModel):
    name: str
    x: list[str]
    y: list[float]


class ChartSpec(BaseModel):
    chart_type: ChartType
    title: str
    x_label: str | None = None
    y_label: str | None = None
    series: list[ChartSeries]
    filename: str = Field(pattern=SAFE_FILENAME_REGEX)


class ChartArtifact(BaseModel):
    filename: str
    path: str = Field(exclude=True)
    chart_type: ChartType
    title: str
    data_points: int
    truncated: bool = False
