"""Generic evaluation runner utilities and latency tracking."""

from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any

from kit.evaluation.models import CaseResult, EvaluationCase, ScoreResult


async def evaluate_async_case(
    case: EvaluationCase,
    fn: Callable[[EvaluationCase], Awaitable[Any]],
    scorers: list[Callable[[Any, dict[str, Any]], list[ScoreResult]]],
) -> CaseResult:
    """Execute an async target function, measure latency, and evaluate scorers."""
    start = perf_counter()
    actual = await fn(case)
    latency = perf_counter() - start

    all_scores: list[ScoreResult] = []
    for scorer in scorers:
        all_scores.extend(scorer(actual, case.expected))

    return CaseResult(
        case_id=case.case_id,
        scores=all_scores,
        latency_seconds=latency,
    )


def evaluate_sync_case(
    case: EvaluationCase,
    fn: Callable[[EvaluationCase], Any],
    scorers: list[Callable[[Any, dict[str, Any]], list[ScoreResult]]],
) -> CaseResult:
    """Execute a synchronous target function, measure latency, and evaluate scorers."""
    start = perf_counter()
    actual = fn(case)
    latency = perf_counter() - start

    all_scores: list[ScoreResult] = []
    for scorer in scorers:
        all_scores.extend(scorer(actual, case.expected))

    return CaseResult(
        case_id=case.case_id,
        scores=all_scores,
        latency_seconds=latency,
    )
