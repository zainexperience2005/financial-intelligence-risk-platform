from typing import Literal

from pydantic import BaseModel, Field


class FinancialAnalysis(BaseModel):
    summary: str = Field(
        description="Concise answer to the user's question."
    )

    reasoning: str = Field(
        description="Brief explanation supporting the answer."
    )

    confidence: Literal["low", "medium", "high"] = Field(
        description="Confidence based only on available evidence."
    )

    requires_data: bool = Field(
        description=(
            "True when answering reliably requires access "
            "to company or transaction data."
        )
    )