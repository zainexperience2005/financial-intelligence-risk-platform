"""Registry contracts use a domain-independent test tool."""

import pytest
from pydantic import BaseModel

from kit.tools import BaseTool, ToolRegistry, ToolResult


class EchoInput(BaseModel):
    value: str


class EchoTool(BaseTool[EchoInput]):
    name = "echo"
    description = "Return the supplied value."
    input_schema = EchoInput

    def execute(self, input_data: EchoInput) -> ToolResult:
        return ToolResult(success=True, data=input_data.value)


def test_register_and_get_tool():
    registry = ToolRegistry()
    tool = EchoTool()
    registry.register(tool)
    assert registry.get("echo") is tool
    assert registry.names() == ["echo"]
    listed = registry.list_tools()
    listed.clear()
    assert registry.list_tools() == [tool]


def test_duplicate_tool_rejected():
    registry = ToolRegistry()
    registry.register(EchoTool())
    with pytest.raises(ValueError, match="already registered"):
        registry.register(EchoTool())


def test_unknown_tool_rejected():
    with pytest.raises(KeyError, match="Unknown tool"):
        ToolRegistry().get("missing")
