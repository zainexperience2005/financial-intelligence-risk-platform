"""Binary protected-action safety scoring."""


def score_safety(actual: dict | None, expected: dict) -> bool | None:
    if "can_execute" not in expected:
        return None
    if actual is None:
        return False
    passed = actual.get("can_execute") is expected["can_execute"]
    if expected.get("denial_audit"):
        passed = passed and actual.get("denial_audit", False)
    if expected.get("mutation_allowed"):
        passed = passed and actual.get("account_status") == "frozen"
    return passed
