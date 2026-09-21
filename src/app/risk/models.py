from typing import Literal

from pydantic import BaseModel, Field


class RiskSignal(BaseModel):
    code: str
    description: str
    points: int = Field(ge=0)


class RiskAssessment(BaseModel):
    score: int = Field(ge=0, le=100)

    level: Literal[
        "low",
        "medium",
        "high",
    ]

    signals: list[RiskSignal] = Field(default_factory=list)
