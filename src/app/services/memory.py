from app.schemas import (
    InvestigationReport,
    RiskAnalysisResult,
)
from kit.memory import MemoryService

memory_service = MemoryService()


def remember_investigation(
    *,
    transaction_id: str,
    report: InvestigationReport,
    risk_analysis: RiskAnalysisResult | None,
) -> str:
    """Explicitly stores an investigation summary in long-term memory."""
    parts = [
        f"Investigation for {transaction_id}.",
        report.executive_summary,
    ]

    if risk_analysis:
        assessment = risk_analysis.assessment
        parts.append(f"Risk level: {assessment.level}. Risk score: {assessment.score}.")

    memory = memory_service.remember(
        content=" ".join(parts),
        memory_type="investigation",
        retention_days=30,
        metadata={
            "transaction_id": transaction_id,
            "source": "investigation_report",
        },
    )

    return memory.memory_id
