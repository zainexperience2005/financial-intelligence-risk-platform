from app.tools import (
    SchemaInspectorInput,
    SchemaInspectorTool,
)


def test_schema_inspector_reads_database() -> None:
    tool = SchemaInspectorTool()

    result = tool.execute(
        SchemaInspectorInput()
    )

    assert result.success is True

    assert "customers" in result.data
    assert "accounts" in result.data
    assert "transactions" in result.data


def test_transaction_schema() -> None:
    tool = SchemaInspectorTool()

    result = tool.execute(
        SchemaInspectorInput(
            table_name="transactions"
        )
    )

    assert result.success is True

    columns = {
        column["name"]
        for column in result.data["transactions"]
    }

    assert "transaction_id" in columns
    assert "amount" in columns
    assert "status" in columns