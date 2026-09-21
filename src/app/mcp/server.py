import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from mcp.server import MCPServer

from app.risk.engine import assess_transaction_risk
from app.tools.safe_sql import SafeSQLTool
from app.tools.schema_inspector import SchemaInspectorTool

mcp = MCPServer("financial-intelligence")

POLICY_DIR = Path("data/policies")
POLICY_MAP = {
    "FIN-POL-001": "transaction_monitoring.md",
    "FIN-POL-002": "failed_transactions.md",
    "FIN-POL-003": "account_restrictions.md",
}


@mcp.tool()
def health_check() -> dict[str, str]:
    """Check whether the financial MCP server is running."""
    return {
        "status": "ok",
        "service": "financial-intelligence",
    }


@mcp.tool()
def assess_risk(
    amount: float,
    status: str,
    failure_reason: str | None = None,
    destination_country: str | None = None,
    customer_country: str | None = None,
) -> dict[str, Any]:
    """Calculate deterministic transaction risk.

    This tool evaluates transaction attributes using the financial platform's
    deterministic risk rules. It does not determine whether fraud occurred.
    """
    assessment = assess_transaction_risk(
        amount=Decimal(str(amount)),
        status=status,
        failure_reason=failure_reason,
        destination_country=destination_country,
        customer_country=customer_country,
    )
    return assessment.model_dump(mode="json")


@mcp.tool()
def query_financial_data(
    query: str,
) -> dict[str, Any]:
    """Execute a validated read-only financial SQL query.

    Only safe SELECT queries are permitted. Mutation statements are rejected.
    """
    tool = SafeSQLTool()
    result = tool.run({"query": query})
    return result.model_dump(mode="json")


@mcp.resource(
    "financial://schema",
    mime_type="application/json",
)
def financial_schema() -> str:
    """Return the readable financial database schema."""
    tool = SchemaInspectorTool()
    result = tool.run({})
    if not result.success:
        return json.dumps({"error": result.error})
    return json.dumps(
        result.data,
        indent=2,
        default=str,
    )


@mcp.resource(
    "financial://policies/{policy_id}",
    mime_type="text/markdown",
)
def financial_policy(
    policy_id: str,
) -> str:
    """Read a financial policy by policy ID."""
    safe_policy_id = policy_id.strip()
    if safe_policy_id not in POLICY_MAP:
        path = POLICY_DIR / f"{safe_policy_id}.md"
        if not path.exists():
            raise ValueError("Unknown policy ID.")
        return path.read_text(encoding="utf-8")

    path = POLICY_DIR / POLICY_MAP[safe_policy_id]
    if not path.exists():
        raise ValueError("Policy document not found.")
    return path.read_text(encoding="utf-8")


@mcp.prompt()
def investigate_transaction(
    transaction_id: str,
) -> str:
    """Create a financial transaction investigation request."""
    return (
        f"Investigate transaction {transaction_id}. "
        "Retrieve the relevant transaction data, "
        "identify applicable financial policies, "
        "assess risk using deterministic risk rules, "
        "state evidence limitations, and produce an "
        "analyst-ready investigation report. "
        "Do not execute customer-impacting actions."
    )


@mcp.prompt()
def explain_transaction_risk(
    transaction_id: str,
) -> str:
    """Create a request to explain transaction risk."""
    return (
        f"Explain the risk assessment for transaction {transaction_id}. "
        "Use verified transaction evidence, "
        "deterministic risk signals, and relevant "
        "policy evidence. A high risk score must "
        "not be described as proof of fraud."
    )
