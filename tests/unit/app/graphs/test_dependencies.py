from app.graphs.dependencies import normalize_plan
from app.schemas.planner import InvestigationPlan


def test_risk_requires_sql():
    plan = InvestigationPlan(
        objective="Assess transaction risk",
        requires_sql=False,
        requires_analytics=False,
        requires_policy=True,
        requires_risk=True,
        requires_action=False,
    )

    normalized = normalize_plan(plan)

    assert normalized.requires_risk is True
    assert normalized.requires_sql is True


def test_analytics_requires_sql():
    plan = InvestigationPlan(
        objective="Analyze failures",
        requires_sql=False,
        requires_analytics=True,
        requires_policy=False,
        requires_risk=False,
        requires_action=False,
    )

    normalized = normalize_plan(plan)

    assert normalized.requires_analytics is True
    assert normalized.requires_sql is True
