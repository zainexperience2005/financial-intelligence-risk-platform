"""Deterministic scoring functions for evaluation."""

from typing import Any

from kit.evaluation.models import ScoreResult


def exact_match(
    *,
    name: str,
    actual: Any,
    expected: Any,
) -> ScoreResult:
    """Evaluate whether actual equals expected deterministically."""
    passed = actual == expected

    return ScoreResult(
        scorer=name,
        score=1.0 if passed else 0.0,
        passed=passed,
        details=(None if passed else f"Expected {expected!r}, received {actual!r}."),
    )


def numeric_match(
    *,
    name: str,
    actual: float | int,
    expected: float | int,
    tolerance: float = 0.0,
) -> ScoreResult:
    """Evaluate whether actual is within numeric tolerance of expected."""
    difference = abs(actual - expected)
    passed = difference <= tolerance

    return ScoreResult(
        scorer=name,
        score=1.0 if passed else 0.0,
        passed=passed,
        details=(
            f"difference={difference}, tolerance={tolerance}" if not passed else None
        ),
    )
