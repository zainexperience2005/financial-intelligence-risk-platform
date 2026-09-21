from unittest.mock import patch

from app.tools.corrective_policy_retrieval import (
    CorrectivePolicyRetrievalInput,
    CorrectivePolicyRetrievalTool,
)
from kit.crag.models import CRAGResult, RetrievalEvaluation
from kit.rag import RetrievedChunk


def test_corrective_policy_retrieval_tool_success():
    evaluation = RetrievalEvaluation(
        relevance="relevant",
        reason="Found restriction rule.",
        useful_chunk_ids=["account_restrictions.md:0"],
    )
    fake_crag_result = CRAGResult(
        chunks=[
            RetrievedChunk(
                content="Human approval is required to freeze accounts.",
                source="account_restrictions.md",
                chunk_id="account_restrictions.md:0",
            )
        ],
        initial_evaluation=evaluation,
        final_evaluation=evaluation,
        original_query="Can AI freeze accounts?",
        final_query="Can AI freeze accounts?",
        correction_used=False,
        retrieval_attempts=1,
    )

    with patch(
        "app.tools.corrective_policy_retrieval.corrective_retrieve",
        return_value=fake_crag_result,
    ):
        tool = CorrectivePolicyRetrievalTool()
        result = tool.execute(
            CorrectivePolicyRetrievalInput(
                query="Can AI freeze accounts?",
                k=4,
            )
        )

    assert result.success is True
    assert result.data["answerable"] is True
    assert result.data["correction_used"] is False
    assert result.data["retrieval_attempts"] == 1
    assert result.data["relevance"] == "relevant"
    assert len(result.data["chunks"]) == 1


def test_corrective_policy_retrieval_tool_failure():
    with patch(
        "app.tools.corrective_policy_retrieval.corrective_retrieve",
        side_effect=Exception("Qdrant service timeout"),
    ):
        tool = CorrectivePolicyRetrievalTool()
        result = tool.execute(
            CorrectivePolicyRetrievalInput(
                query="Any query",
                k=4,
            )
        )

    assert result.success is False
    assert result.error == "Corrective policy retrieval failed."
