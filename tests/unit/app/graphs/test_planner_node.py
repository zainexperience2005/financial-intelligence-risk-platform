from unittest.mock import patch

from app.graphs.nodes import plan_investigation
from app.schemas import InvestigationPlan


def test_plan_investigation_node() -> None:
    fake_plan = InvestigationPlan(
        objective="Analyze transaction failures.",
        requires_sql=True,
        requires_analytics=True,
        requires_policy=False,
        requires_risk=False,
        requires_action=False,
    )

    with patch(
        "app.graphs.nodes.create_investigation_plan",
        return_value=fake_plan,
    ):
        result = plan_investigation(
            {"question": ("Why did transaction failures increase?")}
        )

    assert result["plan"] == fake_plan
    assert result["plan"].requires_sql is True
    assert result["plan"].requires_analytics is True
