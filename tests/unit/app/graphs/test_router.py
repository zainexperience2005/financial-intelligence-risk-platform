from app.graphs.router import route_after_analysis
from app.schemas import FinancialAnalysis


def test_routes_to_data_when_required() -> None:
    state = {
        "question": "Why did failures increase?",
        "analysis": FinancialAnalysis(
            summary="Data is required.",
            reasoning="Company data is unavailable.",
            confidence="low",
            requires_data=True,
        ),
    }

    result = route_after_analysis(state)

    assert result == "data_required"


def test_routes_to_complete_when_data_not_required() -> None:
    state = {
        "question": "What is failure rate?",
        "analysis": FinancialAnalysis(
            summary="Failure rate is a metric.",
            reasoning="This is a conceptual question.",
            confidence="high",
            requires_data=False,
        ),
    }

    result = route_after_analysis(state)

    assert result == "complete"