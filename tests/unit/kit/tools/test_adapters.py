from pydantic import BaseModel, Field

from kit.tools.adapters import to_langchain_tool
from kit.tools.base import BaseTool
from kit.tools.result import ToolResult


class DummyInput(BaseModel):
    value: str = Field(description="A dummy string value")


class DummyTool(BaseTool):
    name: str = "dummy_tool"
    description: str = "A dummy tool for adapter testing"
    input_schema: type[BaseModel] = DummyInput

    def execute(self, input_data: DummyInput) -> ToolResult:
        return ToolResult(
            success=True,
            data={"result": f"processed {input_data.value}"},
        )


def test_to_langchain_tool() -> None:
    tool = DummyTool()
    langchain_tool = to_langchain_tool(tool)

    assert langchain_tool.name == "dummy_tool"
    assert langchain_tool.description == "A dummy tool for adapter testing"

    result = langchain_tool.invoke({"value": "test_input"})
    assert result == {
        "success": True,
        "data": {"result": "processed test_input"},
        "error": None,
    }
