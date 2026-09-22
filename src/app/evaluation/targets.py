"""Evaluation target adapters for the Financial Intelligence platform."""

from typing import Any

from kit.evaluation.models import EvaluationCase


async def evaluate_investigation(
    *,
    case: EvaluationCase,
    investigation_service: Any,
) -> dict[str, Any]:
    """Execute investigation workflow for an evaluation case on an isolated thread."""
    question = case.input.get("question", "")

    response = await investigation_service.investigate(
        question=question,
        thread_id=f"eval-{case.case_id}",
    )

    return {
        "case_id": case.case_id,
        "plan": (
            response.plan.model_dump(mode="json")
            if getattr(response, "plan", None)
            else None
        ),
        "report": (
            response.report.model_dump(mode="json")
            if getattr(response, "report", None)
            else None
        ),
        "sql": (
            response.sql_analysis.model_dump(mode="json")
            if getattr(response, "sql_analysis", None)
            else (
                response.sql.model_dump(mode="json")
                if getattr(response, "sql", None)
                else None
            )
        ),
        "data": (
            response.data_analysis.model_dump(mode="json")
            if getattr(response, "data_analysis", None)
            else None
        ),
        "policy": (
            response.policy_analysis.model_dump(mode="json")
            if getattr(response, "policy_analysis", None)
            else (
                response.policy.model_dump(mode="json")
                if getattr(response, "policy", None)
                else None
            )
        ),
        "risk": (
            response.risk_analysis.model_dump(mode="json")
            if getattr(response, "risk_analysis", None)
            else (
                response.risk.model_dump(mode="json")
                if getattr(response, "risk", None)
                else None
            )
        ),
    }
