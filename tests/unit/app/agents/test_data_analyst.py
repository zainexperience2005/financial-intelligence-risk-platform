from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage

from app.agents.data_analyst import run_data_analyst


def test_data_analyst_returns_direct_summary():
    mock_model = MagicMock()
    mock_model.bind_tools.return_value = mock_model
    mock_model.invoke.return_value = AIMessage(
        content="There are 5 rows provided.",
        tool_calls=[],
    )

    with patch(
        "app.agents.data_analyst.create_chat_model",
        return_value=mock_model,
    ):
        result = run_data_analyst(
            question="Summarize rows",
            rows=[{"amount": 100}],
        )

    assert result.summary == "There are 5 rows provided."
    assert result.source_row_count == 1
    assert result.operation is None
    assert result.result is None


def test_data_analyst_executes_tool_and_returns_aggregation():
    mock_model = MagicMock()
    mock_model.bind_tools.return_value = mock_model

    # Step 1: propose tool call; Step 2: return summary
    mock_model.invoke.side_effect = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "data_analysis",
                    "args": {"operation": "sum", "column": "amount"},
                    "id": "call_123",
                }
            ],
        ),
        AIMessage(
            content="Total sum of transactions is 25000.",
            tool_calls=[],
        ),
    ]

    mock_tool = MagicMock()
    mock_tool.invoke.return_value = {
        "success": True,
        "data": 25000.0,
    }

    with (
        patch(
            "app.agents.data_analyst.create_chat_model",
            return_value=mock_model,
        ),
        patch(
            "app.agents.data_analyst.to_langchain_tool",
            return_value=mock_tool,
        ),
    ):
        result = run_data_analyst(
            question="What is the total sum?",
            rows=[{"amount": 15000}, {"amount": 10000}],
        )

    assert "Total sum" in result.summary
    assert result.operation == "sum"
    assert result.result == 25000.0
    assert result.source_row_count == 2
