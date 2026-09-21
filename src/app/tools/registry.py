from kit.tools import ToolRegistry

from app.tools.schema_inspector import (
    SchemaInspectorTool,
)


def create_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        SchemaInspectorTool()
    )

    return registry