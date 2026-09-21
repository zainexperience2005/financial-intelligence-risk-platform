import pytest

from app.tools import SchemaInspectorTool
from kit.tools import ToolRegistry


def test_register_and_get_tool() -> None:
    registry = ToolRegistry()

    tool = SchemaInspectorTool()

    registry.register(tool)

    assert registry.get(
        "schema_inspector"
    ) is tool


def test_duplicate_tool_rejected() -> None:
    registry = ToolRegistry()

    registry.register(
        SchemaInspectorTool()
    )

    with pytest.raises(ValueError):
        registry.register(
            SchemaInspectorTool()
        )