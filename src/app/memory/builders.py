from typing import Any


def build_investigation_memory(
    *,
    transaction_id: str,
    risk_assessment: Any,
    policy_sources: list[str],
) -> tuple[str, dict[str, str]]:
    """Builds a concise, bounded investigation memory content and metadata tuple."""
    sources = ", ".join(policy_sources)
    if not sources:
        sources = "none"

    content = (
        f"Transaction {transaction_id} was investigated. "
        f"Deterministic risk score: {risk_assessment.score}, "
        f"level: {risk_assessment.level}. "
        f"Policy sources: {sources}."
    )

    metadata = {
        "transaction_id": str(transaction_id),
        "risk_score": str(risk_assessment.score),
        "risk_level": str(risk_assessment.level),
        "ruleset_version": str(risk_assessment.ruleset_version),
        "policy_sources": sources,
    }

    return content, metadata
