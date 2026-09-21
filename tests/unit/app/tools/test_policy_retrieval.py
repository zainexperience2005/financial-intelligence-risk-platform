from unittest.mock import patch

from app.tools.policy_retrieval import (
    PolicyRetrievalInput,
    PolicyRetrievalTool,
)
from kit.rag import RetrievedChunk


def test_policy_retrieval_tool_success():
    fake_chunks = [
        RetrievedChunk(
            content="Transfers over PKR 400,000 require review.",
            source="transaction_monitoring.md",
            chunk_id="transaction_monitoring.md:0",
            score=0.89,
        )
    ]

    with patch(
        "app.tools.policy_retrieval.retrieve_chunks",
        return_value=fake_chunks,
    ):
        tool = PolicyRetrievalTool()
        result = tool.execute(
            PolicyRetrievalInput(
                query="What is the high-value transfer limit?",
                k=2,
            )
        )

    assert result.success is True
    assert len(result.data) == 1
    assert result.data[0]["source"] == "transaction_monitoring.md"
    assert result.data[0]["chunk_id"] == "transaction_monitoring.md:0"


def test_policy_retrieval_tool_handles_failure():
    with patch(
        "app.tools.policy_retrieval.retrieve_chunks",
        side_effect=RuntimeError("Vector database unavailable"),
    ):
        tool = PolicyRetrievalTool()
        result = tool.execute(
            PolicyRetrievalInput(
                query="Any policy question",
                k=4,
            )
        )

    assert result.success is False
    assert result.error == "Policy retrieval failed."
