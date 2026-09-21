from unittest.mock import patch

from app.risk.models import RiskAssessment
from app.schemas import (
    InvestigationReport,
    RiskAnalysisResult,
)
from app.services.memory import remember_investigation


def test_remember_investigation_stores_formatted_summary() -> None:
    report = InvestigationReport(
        executive_summary="TX-1006 involved PKR 475,000 international transfer.",
        findings=["High value transfer to UAE"],
        risk_summary="Medium-high risk.",
        recommendation="Conduct enhanced due diligence.",
        evidence_sufficient=True,
    )

    risk_analysis = RiskAnalysisResult(
        assessment=RiskAssessment(
            score=65,
            level="medium",
            triggered_rules=["international_transfer"],
        ),
        explanation="Medium risk due to threshold breach.",
        evidence_sufficient=True,
    )

    with patch("app.services.memory.memory_service.remember") as mock_remember:

        class FakeRecord:
            memory_id = "mem-mock-123"

        mock_remember.return_value = FakeRecord()

        mem_id = remember_investigation(
            transaction_id="TX-1006",
            report=report,
            risk_analysis=risk_analysis,
        )

        assert mem_id == "mem-mock-123"
        mock_remember.assert_called_once()
        _, kwargs = mock_remember.call_args
        assert "TX-1006" in kwargs["content"]
        assert "Risk level: medium" in kwargs["content"]
        assert "Risk score: 65" in kwargs["content"]
        assert kwargs["memory_type"] == "investigation"
        assert kwargs["metadata"]["transaction_id"] == "TX-1006"
        assert kwargs["metadata"]["source"] == "investigation_report"
