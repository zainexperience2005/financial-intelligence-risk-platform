from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from app.schemas import (
    DataAnalysisResult,
    FinancialAnalysis,
    InvestigationPlan,
    InvestigationReport,
    PolicyAnalysisResult,
    RiskAnalysisResult,
    SQLAnalysisResult,
)


class FinancialState(TypedDict, total=False):
    question: str

    plan: InvestigationPlan | None
    analysis: FinancialAnalysis | None

    sql_analysis: SQLAnalysisResult | None

    data_required: bool
    data_message: str
    data_analysis: DataAnalysisResult | None
    policy_analysis: PolicyAnalysisResult | None
    risk_analysis: RiskAnalysisResult | None
    report: InvestigationReport | None
    messages: Annotated[
        list[AnyMessage],
        add_messages,
    ]
