from pydantic import BaseModel, Field

from app.risk.models import RiskAssessment


class RiskAnalysisResult(BaseModel):
    assessment: RiskAssessment

    explanation: str

    evidence_sufficient: bool

    policy_grounded: bool = False
    """True when policy retrieval was performed and returned grounded results."""

    policy_sources: list[str] = Field(default_factory=list)
