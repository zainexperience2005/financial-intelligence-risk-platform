"""Deterministic analytics and chart consistency scoring."""

from decimal import Decimal, InvalidOperation
from typing import Any


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        normalized = [_normalize(item) for item in value]
        if all(isinstance(item, dict) for item in normalized):
            return sorted(normalized, key=lambda item: repr(item))
        return normalized
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return Decimal(str(value))
    if isinstance(value, str):
        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            return value
    return value


def score_analytics(actual: dict | None, expected: dict) -> bool | None:
    if not expected.get("requires_analytics"):
        return None
    if actual is None:
        return False
    if "expected_result" not in expected:
        return actual.get("operation") == expected.get("operation")
    return _normalize(actual.get("result")) == _normalize(expected["expected_result"])


def score_chart(actual: dict | None, expected: dict) -> bool | None:
    chart_type = expected.get("chart_type")
    if chart_type is None:
        return None
    chart = (actual or {}).get("chart")
    return bool(chart and chart.get("chart_type") == chart_type)
