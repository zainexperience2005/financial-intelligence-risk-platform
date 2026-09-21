from typing import Literal

from app.graphs.state import FinancialState


def route_after_analysis(
    state: FinancialState,
) -> Literal["data_required", "complete"]:
    analysis = state["analysis"]

    if analysis.requires_data:
        return "data_required"

    return "complete"