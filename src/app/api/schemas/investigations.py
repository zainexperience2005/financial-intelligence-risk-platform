from pydantic import BaseModel, Field

from app.schemas.data_analysis import (
    DataAnalysisResult,
)
from app.schemas.planner import (
    InvestigationPlan,
)
from app.schemas.policy_analysis import (
    PolicyAnalysisResult,
)
from app.schemas.report import (
    InvestigationReport,
)
from app.schemas.risk_analysis import (
    RiskAnalysisResult,
)
from app.schemas.sql_analysis import (
    SQLAnalysisResult,
)


class InvestigationRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=4000,
    )

    thread_id: str = Field(
        min_length=1,
        max_length=200,
    )


class InvestigationResponse(BaseModel):
    thread_id: str

    plan: InvestigationPlan | None = None

    report: InvestigationReport | None = None

    sql_analysis: SQLAnalysisResult | None = None

    data_analysis: DataAnalysisResult | None = None

    policy_analysis: PolicyAnalysisResult | None = None

    risk_analysis: RiskAnalysisResult | None = None
