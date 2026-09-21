import pytest

from app.mcp.server import mcp
from kit.mcp.client import MCPClient
from kit.mcp.langchain import load_mcp_tools


@pytest.mark.anyio
async def test_load_mcp_tools():
    client = MCPClient(mcp)
    tools = await load_mcp_tools(client)
    names = {tool.name for tool in tools}
    assert "health_check" in names
    assert "assess_risk" in names
    assert "query_financial_data" in names


@pytest.mark.anyio
async def test_mcp_langchain_risk_tool():
    client = MCPClient(mcp)
    tools = await load_mcp_tools(client)
    risk_tool = next(tool for tool in tools if tool.name == "assess_risk")
    result = await risk_tool.ainvoke(
        {
            "amount": 475000,
            "status": "failed",
            "failure_reason": "risk_review",
            "destination_country": "UAE",
            "customer_country": "Pakistan",
        }
    )
    assert result is not None
