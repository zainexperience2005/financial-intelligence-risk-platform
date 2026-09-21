from pydantic import BaseModel, Field
from sqlalchemy import inspect

from kit.databases import create_database_engine
from kit.tools import BaseTool, ToolResult


class SchemaInspectorInput(BaseModel):
    table_name: str | None = Field(
        default=None,
        description=("Optional table name. If omitted, inspect all available tables."),
    )


# Internal system tables that must never be exposed to the LLM-driven SQL reader
EXCLUDED_TABLES = {
    "approval_requests",
    "audit_events",
    "checkpoint_migrations",
    "checkpoints",
    "checkpoint_blobs",
    "checkpoint_writes",
}


class SchemaInspectorTool(BaseTool[SchemaInspectorInput]):
    name = "schema_inspector"

    description = "Inspect the available financial database schema."

    input_schema = SchemaInspectorInput

    def __init__(self) -> None:
        self._engine = create_database_engine()

    def execute(
        self,
        input_data: SchemaInspectorInput,
    ) -> ToolResult:
        inspector = inspect(self._engine)

        available_tables = [
            t for t in inspector.get_table_names() if t not in EXCLUDED_TABLES
        ]

        if input_data.table_name is not None:
            if input_data.table_name not in available_tables:
                return ToolResult(
                    success=False,
                    error=(f"Unknown table: {input_data.table_name}"),
                )

            tables = [input_data.table_name]

        else:
            tables = available_tables

        schema: dict[str, list[dict[str, str]]] = {}

        for table_name in tables:
            columns = inspector.get_columns(table_name)

            schema[table_name] = [
                {
                    "name": column["name"],
                    "type": str(column["type"]),
                }
                for column in columns
            ]

        return ToolResult(
            success=True,
            data=schema,
        )
