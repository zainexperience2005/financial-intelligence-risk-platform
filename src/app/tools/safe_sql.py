from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.tools.sql_errors import classify_sql_error
from kit.config import get_settings
from kit.databases import create_database_engine
from kit.databases.sql import (
    SQLValidationError,
    apply_row_limit,
    validate_read_only_sql,
)
from kit.tools import BaseTool, ToolResult


class SafeSQLInput(BaseModel):
    query: str = Field(
        min_length=1,
        description=("A single read-only PostgreSQL SELECT query."),
    )


class SafeSQLTool(BaseTool[SafeSQLInput]):
    name = "safe_sql"

    description = (
        "Execute a validated read-only SQL query against the financial database."
    )

    input_schema = SafeSQLInput

    def __init__(
        self,
        max_rows: int = 100,
    ) -> None:
        settings = get_settings()
        self._engine = create_database_engine(
            database_url=settings.read_only_database_url
        )
        self._max_rows = max_rows

    def execute(
        self,
        input_data: SafeSQLInput,
    ) -> ToolResult:
        try:
            statement = validate_read_only_sql(input_data.query)

            safe_query = apply_row_limit(
                statement,
                max_rows=self._max_rows,
            )

            with self._engine.connect() as connection:
                connection.execute(text("SET LOCAL statement_timeout = '5s'"))

                result = connection.execute(text(safe_query))

                rows: list[dict[str, Any]] = [dict(row) for row in result.mappings()]

            return ToolResult(
                success=True,
                data={
                    "query": safe_query,
                    "row_count": len(rows),
                    "rows": rows,
                },
            )

        except SQLValidationError as exc:
            return ToolResult(
                success=False,
                error=str(exc),
            )

        except SQLAlchemyError as exc:
            return ToolResult(
                success=False,
                error=classify_sql_error(exc),
            )
