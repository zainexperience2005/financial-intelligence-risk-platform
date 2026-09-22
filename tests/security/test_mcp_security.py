"""Security tests verifying MCP capability boundaries and SafeSQL delegation."""

import pytest

from app.mcp.server import mcp, query_financial_data


@pytest.mark.anyio
async def test_dangerous_mutations_not_exposed_in_mcp():
    """Verify that actions like freeze_account are not exposed as MCP tools."""
    # List tools declared in the MCPServer
    tool_names = set(mcp._tool_manager._tools.keys())

    assert "freeze_account" not in tool_names
    assert "delete_records" not in tool_names
    assert "update_account" not in tool_names
    assert "unfreeze_account" not in tool_names

    # Verify approved read-only tools ARE present
    assert "query_financial_data" in tool_names
    assert "assess_risk" in tool_names
    assert "health_check" in tool_names


def test_mcp_query_financial_data_enforces_safesql():
    """Verify that MCP tool query_financial_data blocks mutating SQL statements."""
    attack_query = "DELETE FROM accounts WHERE account_id='ACC-1001';"

    res = query_financial_data(attack_query)

    assert res["success"] is False
    assert "error" in res
    error_msg = res["error"]["message"].lower()
    assert "read-only" in error_msg or "only select" in error_msg
