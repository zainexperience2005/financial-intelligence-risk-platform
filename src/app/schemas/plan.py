from pydantic import BaseModel, Field


class InvestigationPlan(BaseModel):
    objective: str = Field(
        description=("A concise description of what the investigation must determine.")
    )

    requires_sql: bool = Field(
        description=("Whether internal structured financial data must be queried.")
    )

    requires_analytics: bool = Field(
        description=(
            "Whether calculations, aggregation, statistics, "
            "or analytical processing are required."
        )
    )

    requires_policy: bool = Field(
        description=(
            "Whether financial policies, rules, or internal "
            "documents must be retrieved."
        )
    )

    requires_risk: bool = Field(
        description=("Whether transaction or customer risk assessment is required.")
    )

    requires_action: bool = Field(
        description=(
            "Whether the request potentially asks the system "
            "to modify or affect a real resource."
        )
    )
