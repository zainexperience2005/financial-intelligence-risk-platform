"""Exact deterministic risk scoring."""


def score_risk(actual: dict | None, expected: dict) -> bool | None:
    if "risk_score" not in expected:
        return None
    if actual is None:
        return False
    signals = sorted(item.get("code") for item in actual.get("signals", []))
    return (
        actual.get("score") == expected["risk_score"]
        and actual.get("level") == expected["risk_level"]
        and signals == sorted(expected.get("expected_signals", []))
    )
