from decimal import Decimal

from pydantic import BaseModel

from app.risk.engine import (
    assess_transaction_risk,
)
from kit.tools import BaseTool, ToolResult


class RiskScoringInput(BaseModel):
    amount: Decimal

    status: str

    failure_reason: str | None = None

    destination_country: str | None = None

    customer_country: str | None = None


class RiskScoringTool(BaseTool[RiskScoringInput]):
    name = "risk_scoring"

    description = (
        "Calculate deterministic transaction risk "
        "signals and a risk score from verified "
        "transaction evidence."
    )

    input_schema = RiskScoringInput

    def execute(
        self,
        input_data: RiskScoringInput,
    ) -> ToolResult:
        assessment = assess_transaction_risk(
            amount=input_data.amount,
            status=input_data.status,
            failure_reason=(input_data.failure_reason),
            destination_country=(input_data.destination_country),
            customer_country=(input_data.customer_country),
        )

        return ToolResult(
            success=True,
            data=assessment.model_dump(mode="json"),
        )
