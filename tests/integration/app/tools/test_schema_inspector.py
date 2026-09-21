"""Inspect real application metadata in an isolated SQLite database."""

import pytest
from sqlalchemy import create_engine

from app.db import Base
from app.tools import SchemaInspectorInput, SchemaInspectorTool


@pytest.fixture
def schema_tool(monkeypatch):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        "app.tools.schema_inspector.create_database_engine", lambda: engine
    )
    yield SchemaInspectorTool()
    engine.dispose()


def test_schema_inspector_reads_database(schema_tool):
    result = schema_tool.execute(SchemaInspectorInput())
    assert result.success
    assert set(result.data) == {"customers", "accounts", "transactions"}


def test_transaction_schema(schema_tool):
    result = schema_tool.execute(SchemaInspectorInput(table_name="transactions"))
    columns = {column["name"]: column["type"] for column in result.data["transactions"]}
    assert {"transaction_id", "amount", "status"} <= columns.keys()
    assert columns["amount"] == "NUMERIC(15, 2)"
