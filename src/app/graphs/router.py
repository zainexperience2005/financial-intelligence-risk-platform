from typing import Literal

from app.graphs.state import FinancialState


def route_after_analysis(
    state: FinancialState,
) -> Literal["data_required", "complete"]:
    analysis = state["analysis"]

    if analysis.requires_data:
        return "data_required"

    return "complete"


def route_after_planning(
    state: FinancialState,
) -> Literal["sql", "analyze"]:
    plan = state["plan"]

    if plan.requires_sql:
        return "sql"

    return "analyze"


def route_after_sql(
    state: FinancialState,
) -> Literal[
    "analytics",
    "analyze",
]:
    plan = state["plan"]

    if plan.requires_analytics:
        return "analytics"

    return "analyze"