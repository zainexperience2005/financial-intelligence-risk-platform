from app.graphs.router import (
    route_after_analysis,
    route_after_analytics,
    route_after_planning,
    route_after_policy,
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
        "question": "What is liquidity?",
        "analysis": FinancialAnalysis(
            summary="Liquidity refers to available cash.",
            reasoning="Sufficient general context available.",
            confidence="high",
            requires_data=False,
        ),
    }

    result = route_after_analysis(state)

    assert result == "complete"


def test_routes_to_sql_when_plan_requires_sql() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="Retrieve transactions.",
            requires_sql=True,
            requires_analytics=False,
            requires_policy=False,
            requires_risk=False,
            requires_action=False,
        ),
    }

    result = route_after_planning(state)

    assert result == "sql"


def test_routes_to_policy_when_plan_requires_policy_without_sql() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="Check policy guidelines directly.",
            requires_sql=False,
            requires_analytics=False,
            requires_policy=True,
            requires_risk=False,
            requires_action=False,
        ),
    }

    result = route_after_planning(state)

    assert result == "policy"


def test_routes_to_report_when_plan_does_not_require_sql_or_policy() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="General financial inquiry.",
            requires_sql=False,
            requires_analytics=False,
            requires_policy=False,
            requires_risk=False,
            requires_action=False,
        ),
    }

    result = route_after_planning(state)

    assert result == "report"


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


def test_routes_to_policy_when_sql_done_and_policy_required_without_analytics() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="Check policy after retrieving transactions.",
            requires_sql=True,
            requires_analytics=False,
            requires_policy=True,
            requires_risk=False,
            requires_action=False,
        ),
    }

    result = route_after_sql(state)

    assert result == "policy"


def test_routes_to_risk_when_sql_done_and_risk_required() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="Score risk directly after SQL.",
            requires_sql=True,
            requires_analytics=False,
            requires_policy=False,
            requires_risk=True,
            requires_action=False,
        ),
    }

    result = route_after_sql(state)

    assert result == "risk"


def test_routes_to_report_when_neither_analytics_nor_policy_nor_risk_needed() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="Inspect raw rows without further processing.",
            requires_sql=True,
            requires_analytics=False,
            requires_policy=False,
            requires_risk=False,
            requires_action=False,
        ),
    }

    result = route_after_sql(state)

    assert result == "report"


def test_routes_to_policy_after_analytics_when_policy_required() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="Evaluate aggregated data against risk policies.",
            requires_sql=True,
            requires_analytics=True,
            requires_policy=True,
            requires_risk=False,
            requires_action=False,
        ),
    }

    result = route_after_analytics(state)

    assert result == "policy"


def test_routes_to_risk_after_analytics_when_risk_required_without_policy() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="Score risk directly after aggregations.",
            requires_sql=True,
            requires_analytics=True,
            requires_policy=False,
            requires_risk=True,
            requires_action=False,
        ),
    }

    result = route_after_analytics(state)

    assert result == "risk"


def test_routes_to_report_after_analytics_when_no_policy_or_risk() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="Complete analysis after calculations.",
            requires_sql=True,
            requires_analytics=True,
            requires_policy=False,
            requires_risk=False,
            requires_action=False,
        ),
    }

    result = route_after_analytics(state)

    assert result == "report"


def test_routes_to_risk_after_policy_when_risk_required() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="Score risk after grounding in policies.",
            requires_sql=True,
            requires_analytics=False,
            requires_policy=True,
            requires_risk=True,
            requires_action=False,
        ),
    }

    result = route_after_policy(state)

    assert result == "risk"


def test_routes_to_report_after_policy_when_risk_not_required() -> None:
    state = {
        "plan": InvestigationPlan(
            objective="Policy investigation without risk scoring.",
            requires_sql=False,
            requires_analytics=False,
            requires_policy=True,
            requires_risk=False,
            requires_action=False,
        ),
    }

    result = route_after_policy(state)

    assert result == "report"
