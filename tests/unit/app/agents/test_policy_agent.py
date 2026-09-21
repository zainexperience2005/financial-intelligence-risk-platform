from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage

from app.agents.policy_agent import run_policy_agent


def test_policy_agent_returns_direct_answer():
    mock_model = MagicMock()
    mock_model.bind_tools.return_value = mock_model
    mock_model.invoke.return_value = AIMessage(
        content="General policy statement.",
        tool_calls=[],
    )

    with patch(
        "app.agents.policy_agent.create_chat_model",
        return_value=mock_model,
    ):
        result = run_policy_agent("What is the general policy?")

    assert result.summary == "General policy statement."
    assert result.grounded is False
    assert result.citations == []
    assert result.retrieved_chunk_count == 0


def test_policy_agent_executes_retrieval_and_extracts_citations():
    mock_model = MagicMock()
    mock_model.bind_tools.return_value = mock_model

    mock_model.invoke.side_effect = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "corrective_policy_retrieval",
                    "args": {"query": "high value transfer rule"},
                    "id": "call_abc",
                }
            ],
        ),
        AIMessage(
            content="Transfers over PKR 400,000 must be flagged for review.",
            tool_calls=[],
        ),
    ]

    mock_tool = MagicMock()
    mock_tool.invoke.return_value = {
        "success": True,
        "data": {
            "answerable": True,
            "correction_used": False,
            "retrieval_attempts": 1,
            "relevance": "relevant",
            "chunks": [
                {
                    "content": (
                        "A transfer with an amount of PKR 400,000 "
                        "or more must be flagged."
                    ),
                    "source": "transaction_monitoring.md",
                    "chunk_id": "transaction_monitoring.md:0",
                }
            ],
        },
    }

    with (
        patch(
            "app.agents.policy_agent.create_chat_model",
            return_value=mock_model,
        ),
        patch(
            "app.agents.policy_agent.to_langchain_tool",
            return_value=mock_tool,
        ),
    ):
        result = run_policy_agent("What is the limit for high value transfers?")

    assert "PKR 400,000" in result.summary
    assert result.grounded is True
    assert len(result.citations) == 1
    assert result.citations[0].source == "transaction_monitoring.md"
    assert result.citations[0].chunk_id == "transaction_monitoring.md:0"
    assert result.retrieval_relevance == "relevant"
    assert result.correction_used is False
    assert result.retrieval_attempts == 1


def test_policy_agent_handles_budget_exhaustion():
    mock_model = MagicMock()
    mock_model.bind_tools.return_value = mock_model

    # Keep returning tool calls
    mock_model.invoke.return_value = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "corrective_policy_retrieval",
                "args": {"query": "repeated query"},
                "id": "call_loop",
            }
        ],
    )

    mock_tool = MagicMock()
    mock_tool.invoke.return_value = {
        "success": True,
        "data": {"chunks": [], "answerable": False},
    }

    with (
        patch(
            "app.agents.policy_agent.create_chat_model",
            return_value=mock_model,
        ),
        patch(
            "app.agents.policy_agent.to_langchain_tool",
            return_value=mock_tool,
        ),
    ):
        result = run_policy_agent("Endless inquiry")

    assert "budget was exhausted" in result.summary.lower()
    assert result.grounded is False
