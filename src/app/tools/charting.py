from pathlib import Path

from pydantic import BaseModel

from kit.charts.matplotlib import (
    ChartValidationError,
    render_chart,
)
from kit.charts.models import ChartSpec
from kit.tools.base import BaseTool
from kit.tools.result import ToolResult

DEFAULT_CHART_OUTPUT_DIR = Path("artifacts/charts")


class ChartInput(BaseModel):
    spec: ChartSpec


class ChartTool(BaseTool[ChartInput]):
    name = "create_chart"

    description = (
        "Creates a chart from already verified structured numeric data. "
        "Accepts a typed ChartSpec (bar or line) and renders a chart image artifact."
    )

    input_schema = ChartInput

    def __init__(
        self,
        output_dir: Path | None = None,
    ) -> None:
        self.output_dir = output_dir or DEFAULT_CHART_OUTPUT_DIR

    def execute(
        self,
        input_data: ChartInput,
    ) -> ToolResult:
        try:
            artifact = render_chart(
                spec=input_data.spec,
                output_dir=self.output_dir,
            )
            return ToolResult(
                success=True,
                data=artifact.model_dump(),
            )
        except (ChartValidationError, ValueError) as exc:
            return ToolResult(
                success=False,
                error=str(exc),
            )
