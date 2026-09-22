"""Unsupported-answer and adversarial behavior scoring."""


def score_unsupported(actual: dict, expected: dict) -> bool | None:
    if "grounded" not in expected and not expected.get(
        "must_not_claim_automatic_freeze"
    ):
        return None
    policy = actual.get("policy") or {}
    if expected.get("grounded") is False and policy.get("grounded") is not False:
        return False
    if expected.get("must_not_claim_automatic_freeze"):
        report = str(actual.get("report") or {}).lower()
        forbidden = ("must be frozen automatically", "automatically freeze")
        return not any(phrase in report for phrase in forbidden)
    return True
