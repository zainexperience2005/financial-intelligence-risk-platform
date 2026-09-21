from pydantic import BaseModel, Field

from kit.tools import BaseTool, ToolResult


class SchemaInspectorInput(BaseModel):
    table_name: str | None = Field(
        default=None,
        description=(
            "Optional table name. If omitted, return "
            "all available tables."
        ),
    )


class SchemaInspectorTool(
    BaseTool[SchemaInspectorInput]
):
    name = "schema_inspector"

    description = (
        "Inspect the available financial database schema."
    )

    input_schema = SchemaInspectorInput

    def execute(
        self,
        input_data: SchemaInspectorInput,
    ) -> ToolResult:
        schema = {
            "customers": [
                "customer_id",
                "name",
                "created_at",
            ],
            "transactions": [
                "transaction_id",
                "customer_id",
                "amount",
                "status",
                "created_at",
            ],
        }

        if input_data.table_name is None:
            return ToolResult(
                success=True,
                data=schema,
            )

        table = schema.get(input_data.table_name)

        if table is None:
            return ToolResult(
                success=False,
                error=(
                    "Unknown table: "
                    f"{input_data.table_name}"
                ),
            )

        return ToolResult(
            success=True,
            data={
                input_data.table_name: table,
            },
        )