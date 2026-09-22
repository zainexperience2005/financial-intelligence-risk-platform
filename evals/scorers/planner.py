"""Deterministic planner scoring."""

PLANNER_FLAGS = {
    "requires_sql",
    "requires_analytics",
    "requires_policy",
    "requires_risk",
    "requires_action",
}


def score_planner(actual: dict | None, expected: dict) -> bool | None:
    required = {key: expected[key] for key in PLANNER_FLAGS if key in expected}
    if not required:
        return None
    if actual is None:
        return False
    return all(actual.get(key) == value for key, value in required.items())
