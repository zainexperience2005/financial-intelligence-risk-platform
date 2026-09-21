"""Unit tests for run_risk_agent — evidence_sufficient semantics (Step 31.1)."""

from unittest.mock import MagicMock, patch

from app.agents.risk_agent import run_risk_agent
from app.schemas import PolicyAnalysisResult, PolicyCitation


def _fake_model_response(text: str = "Risk explanation.") -> MagicMock:
    mock = MagicMock()
    mock.content = text
    return mock


SINGLE_TRANSACTION = {
    "transaction_id": "TX-1006",
    "amount": "475000",
    "status": "failed",
    "failure_reason": "risk_review",
    "destination_country": "UAE",
    "customer_country": "Pakistan",
}


def test_evidence_sufficient_true_without_policy() -> None:
    """evidence_sufficient is True when transaction + deterministic assessment exist,
    even when no policy retrieval was performed."""
    with patch(
        "app.agents.risk_agent.create_chat_model",
        return_value=MagicMock(invoke=MagicMock(return_value=_fake_model_response())),
    ):
        result = run_risk_agent(
            transaction=SINGLE_TRANSACTION,
            customer_country="Pakistan",
            policy_analysis=None,
        )

    assert result.evidence_sufficient is True
    assert result.policy_grounded is False
    assert result.policy_sources == []


def test_evidence_sufficient_true_with_grounded_policy() -> None:
    """evidence_sufficient is True and policy_grounded is True when grounded."""
    grounded_policy = PolicyAnalysisResult(
        summary="Transactions over PKR 400,000 require review.",
        grounded=True,
        citations=[
            PolicyCitation(source="transaction_monitoring.md"),
        ],
    )

    with patch(
        "app.agents.risk_agent.create_chat_model",
        return_value=MagicMock(invoke=MagicMock(return_value=_fake_model_response())),
    ):
        result = run_risk_agent(
            transaction=SINGLE_TRANSACTION,
            customer_country="Pakistan",
            policy_analysis=grounded_policy,
        )

    assert result.evidence_sufficient is True
    assert result.policy_grounded is True
    assert "transaction_monitoring.md" in result.policy_sources


def test_evidence_sufficient_true_with_ungrounded_policy() -> None:
    """evidence_sufficient is True even when policy retrieval is not grounded.
    Policy groundedness is a separate quality signal, not a prerequisite."""
    ungrounded_policy = PolicyAnalysisResult(
        summary="No relevant policy found.",
        grounded=False,
        citations=[],
    )

    with patch(
        "app.agents.risk_agent.create_chat_model",
        return_value=MagicMock(invoke=MagicMock(return_value=_fake_model_response())),
    ):
        result = run_risk_agent(
            transaction=SINGLE_TRANSACTION,
            customer_country="Pakistan",
            policy_analysis=ungrounded_policy,
        )

    assert result.evidence_sufficient is True
    assert result.policy_grounded is False


def test_risk_score_computed_deterministically() -> None:
    """Deterministic risk engine score is always included in the result."""
    with patch(
        "app.agents.risk_agent.create_chat_model",
        return_value=MagicMock(invoke=MagicMock(return_value=_fake_model_response())),
    ):
        result = run_risk_agent(
            transaction=SINGLE_TRANSACTION,
            customer_country="Pakistan",
            policy_analysis=None,
        )

    # TX-1006: HIGH_VALUE(30) + HIGH_VALUE_INTERNATIONAL(25) +
    #          FAILED_TRANSACTION(10) + RISK_REVIEW_FAILURE(25) = 90
    assert result.assessment.score == 90
    assert result.assessment.level == "high"
    codes = {s.code for s in result.assessment.signals}
    assert "HIGH_VALUE" in codes
    assert "HIGH_VALUE_INTERNATIONAL" in codes
    assert "FAILED_TRANSACTION" in codes
    assert "RISK_REVIEW_FAILURE" in codes
