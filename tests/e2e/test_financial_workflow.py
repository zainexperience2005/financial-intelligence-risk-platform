"""Intentionally invoked, provider-backed financial workflow checks."""

import os
from uuid import uuid4

import pytest
from langchain_core.messages import HumanMessage

from app.graphs.financial_graph import build_financial_graph

pytestmark = [pytest.mark.e2e, pytest.mark.llm]


@pytest.mark.asyncio
async def test_financial_investigation_workflow() -> None:
    """Exercise planner through report only when live E2E access is enabled."""
    if os.getenv("RUN_LLM_E2E") != "1":
        pytest.skip("set RUN_LLM_E2E=1 to run the paid full-workflow test")

    graph = build_financial_graph()
    question = "Investigate transaction TX-1006 and explain the verified risk."
    response = await graph.ainvoke(
        {"question": question, "messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": f"e2e-{uuid4()}"}},
    )

    assert response.get("plan") is not None
    assert response.get("report") is not None
    assert response["report"].executive_summary
    assert response.get("risk_analysis") is not None


@pytest.mark.asyncio
async def test_unsupported_policy_question_reports_limitation() -> None:
    """Verify corrective retrieval fails safely when evidence is unavailable."""
    if os.getenv("RUN_LLM_E2E") != "1":
        pytest.skip("set RUN_LLM_E2E=1 to run the paid full-workflow test")

    graph = build_financial_graph()
    question = "What is our cryptocurrency-wallet withdrawal policy?"
    response = await graph.ainvoke(
        {"question": question, "messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": f"e2e-{uuid4()}"}},
    )

    assert response.get("policy_analysis") is not None
    assert response["policy_analysis"].grounded is False
    assert response.get("report") is not None
    assert response["report"].evidence_sufficient is False
