"""Adapter utility to normalize arbitrary tool outputs into ToolResult."""

from typing import Any

from kit.tools.result import ToolResult


def normalize_tool_result(
    value: Any,
) -> ToolResult:
    """Normalize any arbitrary tool return value into a standard ToolResult envelope.

    Allows third-party or LangChain tools returning strings, dicts, or numbers
    to participate cleanly in controlled tool execution pipelines.
    """
    if isinstance(value, ToolResult):
        return value

    return ToolResult.ok(value)
