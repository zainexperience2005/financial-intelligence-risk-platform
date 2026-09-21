"""Unit tests for the investigation evidence bundle builder."""

from app.risk.models import RiskAssessment, RiskSignal
from app.schemas import (
    DataAnalysisResult,
    PolicyAnalysisResult,
    PolicyCitation,
    RiskAnalysisResult,
    SQLAnalysisResult,
)
from app.services.evidence import (
    build_evidence_bundle,
)


def test_build_evidence_with_sql() -> None:
    state = {
        "question": "What happened with transaction TX-1006?",
        "sql_analysis": SQLAnalysisResult(
            summary="One transaction found.",
            sql_query="SELECT * FROM transactions WHERE transaction_id = 'TX-1006'",
            row_count=1,
            rows=[{"transaction_id": "TX-1006", "amount": 475000}],
        ),
    }

    evidence = build_evidence_bundle(state)  # type: ignore[arg-type]

    assert evidence["question"] == "What happened with transaction TX-1006?"
    assert evidence["sql"]["row_count"] == 1
    assert evidence["sql"]["rows"][0]["transaction_id"] == "TX-1006"
    assert "analytics" not in evidence
    assert "policy" not in evidence
    assert "risk" not in evidence


def test_build_evidence_complete_bundle() -> None:
    state = {
        "question": "Assess TX-1006 risk and applicable policies.",
        "sql_analysis": SQLAnalysisResult(
            summary="Found TX-1006.",
            sql_query="SELECT * FROM transactions WHERE transaction_id = 'TX-1006'",
            row_count=1,
            rows=[{"transaction_id": "TX-1006"}],
        ),
        "data_analysis": DataAnalysisResult(
            summary="Transaction amount exceeds 99th percentile.",
            operation="summarize",
        ),
        "policy_analysis": PolicyAnalysisResult(
            summary="Requires compliance officer signoff.",
            grounded=True,
            citations=[
                PolicyCitation(
                    source="transaction_monitoring.md",
                    content="Transactions over PKR 400,000 must be reviewed.",
                )
            ],
        ),
        "risk_analysis": RiskAnalysisResult(
            assessment=RiskAssessment(
                score=90,
                level="high",
                signals=[
                    RiskSignal(
                        code="HIGH_VALUE",
                        description="Transaction exceeds threshold",
                        points=30,
                    )
                ],
            ),
            explanation="High-value flagged transaction.",
            evidence_sufficient=True,
            policy_sources=["transaction_monitoring.md"],
        ),
    }

    evidence = build_evidence_bundle(state)  # type: ignore[arg-type]

    assert evidence["question"] == "Assess TX-1006 risk and applicable policies."
    assert evidence["sql"]["row_count"] == 1
    assert evidence["analytics"]["operation"] == "summarize"
    assert evidence["policy"]["grounded"] is True
    assert evidence["risk"]["assessment"]["score"] == 90
    assert evidence["risk"]["assessment"]["level"] == "high"
