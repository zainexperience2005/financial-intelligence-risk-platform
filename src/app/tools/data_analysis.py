from typing import Any, Literal

from pydantic import BaseModel, Field

from app.analytics.operations import (
    count_by_category,
    group_and_sum,
    summarize_numeric_column,
)
from kit.tools import BaseTool, ToolResult


class DataAnalysisInput(BaseModel):
    operation: Literal[
        "summarize",
        "group_sum",
        "count_by_category",
    ]

    rows: list[dict[str, Any]] = Field(
        description=(
            "Rows previously retrieved from an "
            "approved data source."
        )
    )

    column: str | None = None

    group_by: str | None = None

    value_column: str | None = None


class DataAnalysisTool(
    BaseTool[DataAnalysisInput]
):
    name = "data_analysis"

    description = (
        "Perform deterministic analysis on rows "
        "retrieved from an approved data source."
    )

    input_schema = DataAnalysisInput

    def execute(
        self,
        input_data: DataAnalysisInput,
    ) -> ToolResult:
        try:
            if input_data.operation == "summarize":
                if input_data.column is None:
                    raise ValueError(
                        "column is required for summarize."
                    )

                data = summarize_numeric_column(
                    input_data.rows,
                    input_data.column,
                )

            elif input_data.operation == "group_sum":
                if (
                    input_data.group_by is None
                    or input_data.value_column is None
                ):
                    raise ValueError(
                        "group_by and value_column are "
                        "required for group_sum."
                    )

                data = group_and_sum(
                    input_data.rows,
                    input_data.group_by,
                    input_data.value_column,
                )

            else:
                if input_data.column is None:
                    raise ValueError(
                        "column is required for "
                        "count_by_category."
                    )

                data = count_by_category(
                    input_data.rows,
                    input_data.column,
                )

            return ToolResult(
                success=True,
                data=data,
            )

        except (ValueError, TypeError) as exc:
            return ToolResult(
                success=False,
                error=str(exc),
            )