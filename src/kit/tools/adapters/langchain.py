from langchain_core.tools import StructuredTool

from kit.tools import BaseTool


def to_langchain_tool(
    tool: BaseTool,
) -> StructuredTool:
    def execute_tool(**kwargs):
        input_data = tool.input_schema(**kwargs)

        result = tool.execute(input_data)

        return result.model_dump()

    return StructuredTool.from_function(
        func=execute_tool,
        name=tool.name,
        description=tool.description,
        args_schema=tool.input_schema,
    )
