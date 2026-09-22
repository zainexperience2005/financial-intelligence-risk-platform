"""Policy source and grounding scoring."""

POLICY_SOURCE_FILES = {
    "FIN-POL-001": "transaction_monitoring.md",
    "FIN-POL-002": "failed_transactions.md",
    "FIN-POL-003": "account_restrictions.md",
}


def expected_source_files(expected: dict) -> set[str]:
    return {POLICY_SOURCE_FILES[item] for item in expected.get("policy_ids", [])}


def score_policy_sources(actual: dict | None, expected: dict) -> bool | None:
    sources = expected_source_files(expected)
    if not sources:
        return None
    if actual is None:
        return False
    actual_sources = {item.get("source") for item in actual.get("citations", [])}
    return sources.issubset(actual_sources)


def score_grounding(actual: dict | None, expected: dict) -> bool | None:
    if "grounded" not in expected:
        return None
    return bool(actual and actual.get("grounded")) is bool(expected["grounded"])
