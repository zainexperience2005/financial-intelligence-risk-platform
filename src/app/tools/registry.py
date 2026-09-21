from kit.tools import ToolRegistry

from app.tools.schema_inspector import (
    SchemaInspectorTool,
)
from app.tools.safe_sql import (
    SafeSQLTool,
)
from app.tools.data_analysis import (
    DataAnalysisTool,
)


def create_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        SchemaInspectorTool()
    )
    registry.register(
        SafeSQLTool()
    )
    registry.register(
        DataAnalysisTool()
    )

    return registry