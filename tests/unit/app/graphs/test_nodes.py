from unittest.mock import patch

from app.graphs.nodes import (
    analyze_data,
    analyze_policy,
    analyze_question,
    analyze_risk,
    analyze_sql,
)
from app.risk.models import RiskAssessment
from app.schemas import (
    DataAnalysisResult,
    FinancialAnalysis,
    PolicyAnalysisResult,
    RiskAnalysisResult,
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
        result = analyze_question({"question": "What is transaction failure rate?"})

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
        result = analyze_sql({"question": "How many failed transactions are there?"})

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


def test_analyze_policy_node() -> None:
    fake_policy_result = PolicyAnalysisResult(
        summary="Policy requires enhanced review for transactions over PKR 300,000.",
        grounded=True,
        retrieved_chunk_count=1,
        retrieval_relevance="relevant",
        correction_used=False,
        retrieval_attempts=1,
    )

    with patch(
        "app.graphs.nodes.run_policy_agent",
        return_value=fake_policy_result,
    ):
        result = analyze_policy(
            {
                "question": "What policy applies to transfers over 300k PKR?",
            }
        )

    assert result["policy_analysis"] == fake_policy_result


def test_prepare_turn_resets_specialist_state() -> None:
    from app.graphs.nodes import prepare_turn

    stale_state = {
        "question": "Follow-up inquiry",
        "plan": "old_plan",
        "sql_analysis": "old_sql",
        "data_analysis": "old_data",
        "policy_analysis": "old_policy",
        "risk_analysis": "old_risk",
        "report": "old_report",
    }

    cleaned = prepare_turn(stale_state)  # type: ignore[arg-type]

    assert cleaned["plan"] is None
    assert cleaned["sql_analysis"] is None
    assert cleaned["data_analysis"] is None
    assert cleaned["policy_analysis"] is None
    assert cleaned["risk_analysis"] is None
    assert cleaned["report"] is None


def test_create_report_node_appends_aimessage() -> None:
    from app.graphs.nodes import create_report
    from app.schemas.report import InvestigationReport

    fake_report = InvestigationReport(
        executive_summary="Executive summary test.",
        findings=["Finding 1"],
        risk_summary="Risk is low.",
        recommendation="Continue standard monitoring.",
        evidence_sufficient=True,
    )

    with patch(
        "app.graphs.nodes.create_investigation_report",
        return_value=fake_report,
    ):
        result = create_report({"question": "Investigate ACC-1001"})

    assert result["report"] == fake_report
    assert len(result["messages"]) == 1
    assert result["messages"][0].content == "Executive summary test."


# ---------------------------------------------------------------------------
# analyze_risk node — 31.2 multi-transaction guard & evidence_sufficient fix
# ---------------------------------------------------------------------------


def _make_risk_result(
    *, evidence_sufficient: bool, policy_grounded: bool
) -> RiskAnalysisResult:
    return RiskAnalysisResult(
        assessment=RiskAssessment(score=30, level="low", signals=[]),
        explanation="Low risk.",
        evidence_sufficient=evidence_sufficient,
        policy_grounded=policy_grounded,
    )


def test_analyze_risk_node_single_row_runs_agent() -> None:
    """Risk analysis runs normally when exactly one transaction row is returned."""
    fake_sql = SQLAnalysisResult(
        summary="One transaction found.",
        row_count=1,
        rows=[{"transaction_id": "TX-001", "amount": "10000", "status": "completed"}],
    )
    fake_result = _make_risk_result(evidence_sufficient=True, policy_grounded=False)

    with patch(
        "app.graphs.nodes.run_risk_agent",
        return_value=fake_result,
    ):
        result = analyze_risk(
            {
                "question": "What is the risk for TX-001?",
                "sql_analysis": fake_sql,
            }
        )

    assert result["risk_analysis"] == fake_result


def test_analyze_risk_node_multi_row_skips_risk() -> None:
    """Risk analysis is skipped for multi-row results (ambiguous scope)."""
    fake_sql = SQLAnalysisResult(
        summary="Multiple transactions found.",
        row_count=3,
        rows=[
            {"transaction_id": "TX-001", "amount": "10000", "status": "completed"},
            {"transaction_id": "TX-002", "amount": "20000", "status": "failed"},
            {"transaction_id": "TX-003", "amount": "5000", "status": "completed"},
        ],
    )

    result = analyze_risk(
        {
            "question": "What are the recent transactions?",
            "sql_analysis": fake_sql,
        }
    )

    assert result == {}


def test_analyze_risk_node_no_sql_skips_risk() -> None:
    """Risk analysis is skipped when sql_analysis is None."""
    result = analyze_risk(
        {
            "question": "Generic question",
            "sql_analysis": None,
        }
    )

    assert result == {}


def test_analyze_risk_node_empty_rows_skips_risk() -> None:
    """Risk analysis is skipped when sql_analysis has no rows."""
    fake_sql = SQLAnalysisResult(
        summary="No transactions found.",
        row_count=0,
        rows=[],
    )

    result = analyze_risk(
        {
            "question": "TX-999 risk?",
            "sql_analysis": fake_sql,
        }
    )

    assert result == {}
