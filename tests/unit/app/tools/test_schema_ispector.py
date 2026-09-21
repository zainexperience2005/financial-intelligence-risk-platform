from app.tools import (
    SchemaInspectorInput,
    SchemaInspectorTool,
)


def test_schema_inspector_lists_tables() -> None:
    tool = SchemaInspectorTool()

    result = tool.execute(
        SchemaInspectorInput()
    )

    assert result.success is True
    assert "customers" in result.data
    assert "transactions" in result.data


def test_schema_inspector_returns_table() -> None:
    tool = SchemaInspectorTool()

    result = tool.execute(
        SchemaInspectorInput(
            table_name="transactions"
        )
    )

    assert result.success is True
    assert "transactions" in result.data


def test_schema_inspector_unknown_table() -> None:
    tool = SchemaInspectorTool()

    result = tool.execute(
        SchemaInspectorInput(
            table_name="unknown"
        )
    )

    assert result.success is False
    assert result.error is not None