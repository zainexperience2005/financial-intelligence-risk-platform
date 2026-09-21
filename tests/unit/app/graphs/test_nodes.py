from unittest.mock import patch

from app.graphs.nodes import analyze_question
from app.schemas import FinancialAnalysis


def test_analyze_question_node() -> None:
    fake_analysis = FinancialAnalysis(
        summary="Transaction failure rate measures failures.",
        reasoning="It compares failed transactions with attempts.",
        confidence="high",
        requires_data=False,
    )

    with patch(
        "app.graphs.nodes.ask_financial_assistant",
        return_value=fake_analysis,
    ):
        result = analyze_question(
            {
                "question": "What is transaction failure rate?"
            }
        )

    assert result["analysis"] == fake_analysis