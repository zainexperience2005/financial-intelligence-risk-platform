from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.data_analysis import DataAnalysisResult
from app.schemas.plan import InvestigationPlan
from app.schemas.policy_analysis import PolicyAnalysisResult
from app.schemas.risk_analysis import RiskAnalysisResult
from app.schemas.sql_analysis import SQLAnalysisResult


class EvidenceReference(BaseModel):
    evidence_type: Literal[
        "sql",
        "analytics",
        "policy",
        "risk",
    ]

    reference: str


class InvestigationReport(BaseModel):
    executive_summary: str

    findings: list[str] = Field(default_factory=list)

    risk_summary: str | None = None

    recommendation: str | None = None

    evidence_sufficient: bool

    evidence_references: list[EvidenceReference] = Field(default_factory=list)

    limitations: list[str] = Field(default_factory=list)


class InvestigationResponse(BaseModel):
    plan: InvestigationPlan

    report: InvestigationReport

    sql_analysis: SQLAnalysisResult | None = None

    data_analysis: DataAnalysisResult | None = None

    policy_analysis: PolicyAnalysisResult | None = None

    risk_analysis: RiskAnalysisResult | None = None
