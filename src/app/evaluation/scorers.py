"""Domain-specific evaluation scorers for financial risk, policy, and compliance."""

from app.risk.models import RiskAssessment
from kit.evaluation.models import ScoreResult
from kit.evaluation.scorers import exact_match, numeric_match


def score_risk_assessment(
    *,
    actual: RiskAssessment,
    expected_score: int,
    expected_level: str,
    expected_signals: list[str] | None = None,
) -> list[ScoreResult]:
    """Score a RiskAssessment output against deterministic expected values."""
    results = [
        numeric_match(
            name="risk_score",
            actual=actual.score,
            expected=expected_score,
            tolerance=0.0,
        ),
        exact_match(
            name="risk_level",
            actual=actual.level,
            expected=expected_level,
        ),
    ]

    if expected_signals is not None:
        actual_signals = [s.code for s in actual.signals]
        passed = sorted(actual_signals) == sorted(expected_signals)
        results.append(
            ScoreResult(
                scorer="risk_signals",
                score=1.0 if passed else 0.0,
                passed=passed,
                details=(
                    None
                    if passed
                    else (
                        f"Expected signals {expected_signals!r}, got {actual_signals!r}"
                    )
                ),
            )
        )

    return results


def score_expected_sources(
    *,
    actual_sources: list[str],
    expected_sources: list[str],
) -> ScoreResult:
    """Evaluate source recall: whether expected sources are in citations."""
    actual = set(actual_sources)
    expected = set(expected_sources)

    passed = expected.issubset(actual)

    if not expected:
        score = 1.0
    else:
        score = len(expected & actual) / len(expected)

    return ScoreResult(
        scorer="expected_sources",
        score=score,
        passed=passed,
        details=f"expected={sorted(expected)}, actual={sorted(actual)}",
    )


def score_unsupported_grounding(
    *,
    grounded: bool,
    expected_grounded: bool = False,
) -> ScoreResult:
    """Evaluate whether an unsupported inquiry correctly reports lack of grounding."""
    passed = grounded == expected_grounded
    return ScoreResult(
        scorer="unsupported_grounding",
        score=1.0 if passed else 0.0,
        passed=passed,
        details=(
            None
            if passed
            else f"Expected grounded={expected_grounded}, but got grounded={grounded}"
        ),
    )
