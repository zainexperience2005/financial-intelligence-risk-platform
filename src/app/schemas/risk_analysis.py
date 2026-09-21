from pydantic import BaseModel, Field

from app.risk.models import RiskAssessment


class RiskAnalysisResult(BaseModel):
    assessment: RiskAssessment

    explanation: str

    evidence_sufficient: bool

    policy_sources: list[str] = Field(default_factory=list)
