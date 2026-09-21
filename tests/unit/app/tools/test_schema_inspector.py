"""Unit tests replace SQLAlchemy inspection; no database is contacted."""

from unittest.mock import Mock, patch

import pytest

from app.tools import SchemaInspectorInput, SchemaInspectorTool


@pytest.fixture
def inspector():
    fake = Mock()
    fake.get_table_names.return_value = ["customers", "transactions"]
    fake.get_columns.return_value = [{"name": "amount", "type": "NUMERIC(15, 2)"}]
    with patch("app.tools.schema_inspector.inspect", return_value=fake):
        yield fake


def test_lists_tables(inspector):
    result = SchemaInspectorTool().execute(SchemaInspectorInput())
    assert result.success
    assert set(result.data) == {"customers", "transactions"}
    assert inspector.get_columns.call_count == 2


def test_selected_table(inspector):
    result = SchemaInspectorTool().execute(
        SchemaInspectorInput(table_name="transactions")
    )
    assert result.data == {
        "transactions": [{"name": "amount", "type": "NUMERIC(15, 2)"}]
    }
    inspector.get_columns.assert_called_once_with("transactions")


def test_unknown_table(inspector):
    result = SchemaInspectorTool().execute(SchemaInspectorInput(table_name="unknown"))
    assert not result.success
    assert result.error == "Unknown table: unknown"
    inspector.get_columns.assert_not_called()
