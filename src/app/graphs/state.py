from typing import TypedDict

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

    plan: InvestigationPlan
    analysis: FinancialAnalysis

    sql_analysis: SQLAnalysisResult

    data_required: bool
    data_message: str
    data_analysis: DataAnalysisResult
    policy_analysis: PolicyAnalysisResult
    risk_analysis: RiskAnalysisResult
    report: InvestigationReport
