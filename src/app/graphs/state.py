from typing import TypedDict

from app.schemas import FinancialAnalysis


class FinancialState(TypedDict, total=False):
    question: str
    analysis: FinancialAnalysis