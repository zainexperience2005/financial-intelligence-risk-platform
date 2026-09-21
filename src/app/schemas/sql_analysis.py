from typing import Any

from pydantic import BaseModel, Field


class SQLAnalysisResult(BaseModel):
    summary: str = Field(
        description=(
            "A concise explanation of what the "
            "database evidence shows."
        )
    )

    sql_query: str | None = Field(
        default=None,
        description=(
            "The final read-only SQL query used "
            "for the investigation."
        ),
    )

    row_count: int = Field(
        default=0,
        ge=0,
    )

    rows: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    tool_iterations: int = Field(
        default=0,
        ge=0,
    )

    sql_attempts: int = Field(
        default=0,
        ge=0,
    )

    failed_sql_attempts: int = Field(
        default=0,
        ge=0,
    )