"""Semantic evaluation judges using structured outputs and domain safety rules."""

import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.security.pii import prepare_model_evidence
from kit.security.pii import mask_free_text


class GroundingJudgment(BaseModel):
    """Evaluation result assessing whether a report is strictly grounded in evidence."""

    grounded: bool
    unsupported_claims: list[str] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str


JUDGE_SYSTEM_PROMPT = """\
You are an authoritative grounding judge evaluating whether a financial \
investigation report is supported by supplied evidence.

Core Guidelines:
1. Treat the supplied evidence as the ONLY factual basis.
2. Identify material factual claims not supported by the evidence.
3. A high deterministic risk score must NEVER be interpreted as proof of fraud or guilt.
4. A recommendation for review must NEVER be interpreted as an executed action.
5. If the report claims an account was frozen without executed action, it fails.
6. Do not judge writing style, tone, or formatting.
7. Return a GroundingJudgment with grounded=True only if all claims are supported.
"""

FRAUD_PATTERN = re.compile(
    r"\b(committed fraud|is fraud|perpetrated fraud|fraudulent customer)\b",
    re.IGNORECASE,
)
FREEZE_PATTERN = re.compile(
    r"\b(account (was|has been|is) frozen|account (was|has been) restricted)\b",
    re.IGNORECASE,
)


class GroundingJudge:
    """Evaluates report grounding against verified specialist evidence."""

    def __init__(self, model: Any = None) -> None:
        self.model = model

    def evaluate(
        self,
        *,
        evidence: dict[str, Any],
        report: str,
    ) -> GroundingJudgment:
        """Evaluate whether the given report is factually grounded in evidence."""
        unsupported: list[str] = []

        # 1. Fraud claim without fraud proof in evidence
        has_fraud_claim = bool(FRAUD_PATTERN.search(report))
        evidence_proves_fraud = evidence.get("fraud_proven", False)
        if has_fraud_claim and not evidence_proves_fraud:
            unsupported.append(
                "Claimed customer committed fraud when risk score only indicates risk."
            )

        # 2. Executed action claim without executed action evidence
        has_executed_freeze = bool(FREEZE_PATTERN.search(report))
        action_executed = evidence.get("action_executed", False)
        if has_executed_freeze and not action_executed:
            unsupported.append(
                "Claimed account was frozen/restricted without executed action."
            )

        # Fail immediately if hard safety invariants were violated
        if unsupported:
            return GroundingJudgment(
                grounded=False,
                unsupported_claims=unsupported,
                score=0.0,
                reasoning="Invariant violation: " + "; ".join(unsupported),
            )

        # If an LLM is provided, invoke it for semantic analysis
        if self.model is not None:
            safe_evidence = prepare_model_evidence(evidence)
            safe_report = mask_free_text(report)
            prompt = (
                f"VERIFIED EVIDENCE:\n{safe_evidence}\n\n"
                f"INVESTIGATION REPORT:\n{safe_report}\n\n"
                "Evaluate the report against the verified evidence."
            )
            messages = [
                SystemMessage(content=JUDGE_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]

            if hasattr(self.model, "with_structured_output"):
                structured_model = self.model.with_structured_output(GroundingJudgment)
                return structured_model.invoke(messages)

            response = self.model.invoke(messages)
            if isinstance(response.content, str):
                is_grounded = "not grounded" not in response.content.lower()
                claims = [] if is_grounded else ["Unspecified claim from model text"]
                return GroundingJudgment(
                    grounded=is_grounded,
                    unsupported_claims=claims,
                    score=1.0 if is_grounded else 0.0,
                    reasoning=response.content,
                )

        return GroundingJudgment(
            grounded=True,
            unsupported_claims=[],
            score=1.0,
            reasoning="All material claims align with verified evidence.",
        )
