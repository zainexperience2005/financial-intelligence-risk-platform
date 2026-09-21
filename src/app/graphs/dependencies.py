from app.schemas.planner import (
    InvestigationPlan,
)


def normalize_plan(
    plan: InvestigationPlan,
) -> InvestigationPlan:
    updates: dict[str, bool] = {}

    if plan.requires_analytics:
        updates["requires_sql"] = True

    if plan.requires_risk:
        updates["requires_sql"] = True

    if not updates:
        return plan

    return plan.model_copy(update=updates)
