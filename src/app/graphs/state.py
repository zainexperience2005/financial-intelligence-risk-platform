from app.schemas import DataAnalysisResult
from typing import TypedDict

from app.schemas import (
    FinancialAnalysis,
    InvestigationPlan,
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