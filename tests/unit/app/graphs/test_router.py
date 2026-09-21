from app.graphs.router import (
    route_after_analysis,
    route_after_planning,
    route_after_sql,
)
from app.schemas import (
    FinancialAnalysis,
    InvestigationPlan,
)


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


def test_routes_to_sql_when_plan_requires_sql() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="Query database for failed transactions.",
            requires_sql=True,
            requires_analytics=False,
            requires_policy=False,
            requires_risk=False,
            requires_action=False,
        ),
    }

    result = route_after_planning(state)

    assert result == "sql"


def test_routes_to_analyze_when_plan_does_not_require_sql() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="Explain financial concept.",
            requires_sql=False,
            requires_analytics=False,
            requires_policy=False,
            requires_risk=False,
            requires_action=False,
        ),
    }

    result = route_after_planning(state)

    assert result == "analyze"


def test_routes_to_analytics_when_plan_requires_analytics() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="Analyze failure distributions.",
            requires_sql=True,
            requires_analytics=True,
            requires_policy=False,
            requires_risk=False,
            requires_action=False,
        ),
    }

    result = route_after_sql(state)

    assert result == "analytics"


def test_routes_to_analyze_when_plan_does_not_require_analytics() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="Inspect raw rows.",
            requires_sql=True,
            requires_analytics=False,
            requires_policy=False,
            requires_risk=False,
            requires_action=False,
        ),
    }

    result = route_after_sql(state)

    assert result == "analyze"