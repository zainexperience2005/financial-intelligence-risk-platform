from typing import Any

from mcp import Client
from mcp.types import Tool


class MCPClient:
    def __init__(
        self,
        target: Any,
    ) -> None:
        self._target = target

    def client(self) -> Client:
        return Client(self._target)

    async def list_tools(
        self,
    ) -> list[Tool]:
        async with self.client() as client:
            result = await client.list_tools()
            return result.tools

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ):
        async with self.client() as client:
            return await client.call_tool(
                name,
                arguments,
            )
