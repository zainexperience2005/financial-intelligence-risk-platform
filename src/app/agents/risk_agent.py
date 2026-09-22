import json
from decimal import Decimal
from typing import Any

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)

from app.prompts.risk_agent import (
    RISK_AGENT_SYSTEM_PROMPT,
)
from app.risk.engine import (
    assess_transaction_risk,
)
from app.schemas import (
    PolicyAnalysisResult,
    RiskAnalysisResult,
)
from app.security.pii import prepare_model_evidence
from kit.llms import create_chat_model


def run_risk_agent(
    *,
    transaction: dict[str, Any],
    customer_country: str | None,
    policy_analysis: PolicyAnalysisResult | None,
) -> RiskAnalysisResult:
    assessment = assess_transaction_risk(
        amount=Decimal(str(transaction["amount"])),
        status=str(transaction["status"]),
        failure_reason=transaction.get("failure_reason"),
        destination_country=transaction.get("destination_country"),
        customer_country=customer_country,
    )

    policy_sources = []

    if policy_analysis:
        policy_sources = sorted(
            {citation.source for citation in policy_analysis.citations}
        )

    # Evidence is sufficient when we have the transaction row and a deterministic
    # risk assessment — the only required authoritative inputs for risk scoring.
    # Policy retrieval enriches the explanation but is not a prerequisite for a
    # valid risk result; it is tracked separately via policy_grounded.
    policy_grounded = bool(policy_analysis and policy_analysis.grounded)
    evidence_sufficient = bool(transaction and assessment)

    model = create_chat_model()

    evidence = {
        "transaction": transaction,
        "risk_assessment": (assessment.model_dump(mode="json")),
        "policy_summary": (policy_analysis.summary if policy_analysis else None),
        "policy_sources": policy_sources,
        "policy_grounded": policy_grounded,
    }

    safe_evidence = prepare_model_evidence(evidence)

    response = model.invoke(
        [
            SystemMessage(content=RISK_AGENT_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "Explain this risk assessment "
                    "using only the supplied evidence.\n\n"
                    + json.dumps(
                        safe_evidence,
                        indent=2,
                        default=str,
                    )
                ),
            ),
        ]
    )

    return RiskAnalysisResult(
        assessment=assessment,
        explanation=str(response.content),
        evidence_sufficient=evidence_sufficient,
        policy_grounded=policy_grounded,
        policy_sources=policy_sources,
    )
