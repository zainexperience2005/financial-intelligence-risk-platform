import pytest
from mcp import Client

from app.mcp.server import mcp
from kit.mcp import MCPClient


@pytest.mark.anyio
async def test_mcp_health_check():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "health_check",
            {},
        )
        assert result.is_error is False


@pytest.mark.anyio
async def test_mcp_risk_tool():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "assess_risk",
            {
                "amount": 475000,
                "status": "failed",
                "failure_reason": "risk_review",
                "destination_country": "UAE",
                "customer_country": "Pakistan",
            },
        )
        assert result.is_error is False


@pytest.mark.anyio
async def test_mcp_query_financial_data_tool():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "query_financial_data",
            {
                "query": "SELECT count(*) FROM transactions",
            },
        )
        assert result.is_error is False


@pytest.mark.anyio
async def test_mcp_tool_discovery():
    async with Client(mcp) as client:
        result = await client.list_tools()
        tools = result.tools if hasattr(result, "tools") else result
        names = {tool.name for tool in tools}
        assert "health_check" in names
        assert "assess_risk" in names
        assert "query_financial_data" in names


@pytest.mark.anyio
async def test_mcp_capability_discovery():
    async with Client(mcp) as client:
        tools_res = await client.list_tools()
        resources_res = await client.list_resources()
        templates_res = await client.list_resource_templates()
        prompts_res = await client.list_prompts()

        tools = tools_res.tools if hasattr(tools_res, "tools") else tools_res
        resources = (
            resources_res.resources
            if hasattr(resources_res, "resources")
            else resources_res
        )
        templates = (
            templates_res.resource_templates
            if hasattr(templates_res, "resource_templates")
            else templates_res
        )
        prompts = (
            prompts_res.prompts if hasattr(prompts_res, "prompts") else prompts_res
        )

        tool_names = {tool.name for tool in tools}
        resource_uris = {str(resource.uri) for resource in resources}
        template_uris = {template.uri_template for template in templates}
        prompt_names = {prompt.name for prompt in prompts}

        assert "query_financial_data" in tool_names
        assert "financial://schema" in resource_uris
        assert any("financial://policies/" in uri for uri in template_uris)
        assert "investigate_transaction" in prompt_names
        assert "explain_transaction_risk" in prompt_names


@pytest.mark.anyio
async def test_read_schema_resource():
    async with Client(mcp) as client:
        result = await client.read_resource("financial://schema")
        assert result.contents


@pytest.mark.anyio
async def test_read_policy_resource():
    async with Client(mcp) as client:
        result = await client.read_resource("financial://policies/FIN-POL-001")
        assert result.contents


@pytest.mark.anyio
async def test_investigation_prompt():
    async with Client(mcp) as client:
        result = await client.get_prompt(
            "investigate_transaction",
            arguments={
                "transaction_id": "TX-1006",
            },
        )
        assert result.messages


@pytest.mark.anyio
async def test_explain_transaction_risk_prompt():
    async with Client(mcp) as client:
        result = await client.get_prompt(
            "explain_transaction_risk",
            arguments={
                "transaction_id": "TX-1006",
            },
        )
        assert result.messages


@pytest.mark.anyio
async def test_kit_mcp_client():
    mcp_client = MCPClient(mcp)
    async with mcp_client.client() as client:
        tools_res = await client.list_tools()
        tools = tools_res.tools if hasattr(tools_res, "tools") else tools_res
        tool_names = {tool.name for tool in tools}
        assert "health_check" in tool_names
        assert "query_financial_data" in tool_names
