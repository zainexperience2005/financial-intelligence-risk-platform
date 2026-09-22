"""Result-based SQL evaluation without query string equality."""

from kit.databases.sql import SQLValidationError, validate_read_only_sql


def score_sql(actual: dict | None, expected: dict) -> bool | None:
    if not expected.get("requires_sql"):
        return None
    if actual is None or not actual.get("sql_query"):
        return False
    try:
        validate_read_only_sql(actual["sql_query"])
    except SQLValidationError:
        return False

    rows = actual.get("rows", [])
    if expected.get("record_found") is False:
        return len(rows) == 0

    expected_ids = set(expected.get("expected_transaction_ids", []))
    if expected_ids:
        actual_ids = {str(row.get("transaction_id")) for row in rows}
        return expected_ids == actual_ids
    return True
