from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import create_model

from kit.mcp.client import MCPClient

JSON_TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def schema_to_model(
    name: str,
    schema: dict[str, Any],
):
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    fields: dict[str, tuple[type, Any]] = {}

    for field_name, field_schema in properties.items():
        json_type = field_schema.get("type")
        if not json_type and "anyOf" in field_schema:
            types = [
                t.get("type") for t in field_schema["anyOf"] if t.get("type") != "null"
            ]
            json_type = types[0] if types else "string"
        elif not json_type:
            json_type = "string"

        python_type = JSON_TYPE_MAP.get(json_type, Any)
        if field_name in required:
            fields[field_name] = (python_type, ...)
        else:
            fields[field_name] = (
                python_type | None,
                field_schema.get("default", None),
            )

    return create_model(f"{name}Input", **fields)


async def convert_mcp_tool(
    mcp_client: MCPClient,
    mcp_tool: Any,
) -> StructuredTool:
    input_schema = getattr(
        mcp_tool,
        "input_schema",
        getattr(mcp_tool, "inputSchema", {}),
    )
    args_schema = schema_to_model(
        mcp_tool.name,
        input_schema,
    )

    async def call_mcp_tool(
        **kwargs: Any,
    ) -> Any:
        result = await mcp_client.call_tool(
            mcp_tool.name,
            kwargs,
        )
        if result.is_error:
            messages: list[str] = []
            for block in result.content:
                text = getattr(block, "text", None)
                if text:
                    messages.append(text)
            error_message = "\n".join(messages) or "MCP tool execution failed."
            raise RuntimeError(error_message)

        if result.structured_content is not None:
            return result.structured_content

        texts: list[str] = []
        for block in result.content:
            text = getattr(block, "text", None)
            if text is not None:
                texts.append(text)
        return "\n".join(texts)

    return StructuredTool.from_function(
        coroutine=call_mcp_tool,
        name=mcp_tool.name,
        description=(mcp_tool.description or f"MCP tool {mcp_tool.name}"),
        args_schema=args_schema,
    )


async def load_mcp_tools(
    mcp_client: MCPClient,
) -> list[StructuredTool]:
    discovered = await mcp_client.list_tools()
    tools: list[StructuredTool] = []
    for mcp_tool in discovered:
        tool = await convert_mcp_tool(
            mcp_client,
            mcp_tool,
        )
        tools.append(tool)
    return tools
