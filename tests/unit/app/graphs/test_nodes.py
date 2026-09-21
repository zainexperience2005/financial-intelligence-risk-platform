from unittest.mock import patch

from app.graphs.nodes import (
    analyze_data,
    analyze_question,
    analyze_sql,
)
from app.schemas import (
    DataAnalysisResult,
    FinancialAnalysis,
    SQLAnalysisResult,
)


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


def test_analyze_sql_node() -> None:
    fake_sql_result = SQLAnalysisResult(
        summary="There are 3 failed transactions.",
        sql_query="SELECT count(*) FROM transactions WHERE status = 'failed'",
        row_count=1,
        rows=[{"count": 3}],
    )

    with patch(
        "app.graphs.nodes.run_sql_analyst",
        return_value=fake_sql_result,
    ):
        result = analyze_sql(
            {
                "question": "How many failed transactions are there?"
            }
        )

    assert result["sql_analysis"] == fake_sql_result


def test_analyze_data_node() -> None:
    fake_data_result = DataAnalysisResult(
        summary="Total sum calculated.",
        operation="sum",
        result=1500.0,
        source_row_count=2,
    )

    fake_sql_result = SQLAnalysisResult(
        summary="Retrieved rows.",
        row_count=2,
        rows=[{"amount": 1000.0}, {"amount": 500.0}],
    )

    with patch(
        "app.graphs.nodes.run_data_analyst",
        return_value=fake_data_result,
    ):
        result = analyze_data(
            {
                "question": "What is the total amount?",
                "sql_analysis": fake_sql_result,
            }
        )

    assert result["data_analysis"] == fake_data_result


def test_analyze_data_node_without_sql_analysis() -> None:
    result = analyze_data(
        {
            "question": "What is the total amount?",
            "sql_analysis": None,
        }
    )

    assert result == {}