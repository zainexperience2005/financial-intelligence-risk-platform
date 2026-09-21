from app.tools.data_analysis import (
    DataAnalysisTool,
)
from app.tools.safe_sql import (
    SafeSQLTool,
)
from app.tools.schema_inspector import (
    SchemaInspectorTool,
)
from kit.tools import ToolRegistry


def create_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(SchemaInspectorTool())
    registry.register(SafeSQLTool())
    registry.register(DataAnalysisTool())

    return registry
