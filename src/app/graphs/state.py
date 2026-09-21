from typing import TypedDict

from app.schemas import (
    FinancialAnalysis,
    InvestigationPlan,
)


class FinancialState(TypedDict, total=False):
    question: str

    plan: InvestigationPlan

    analysis: FinancialAnalysis

    data_required: bool
    data_message: str