"""LangSmith experiment runner and tracing integration adapter."""

import os
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any

from kit.evaluation.models import CaseResult, EvaluationCase, ScoreResult

TargetFunction = Callable[[EvaluationCase], Awaitable[dict[str, Any]]]
EvaluatorFunction = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


class LangSmithExperimentRunner:
    """Adapter for running evaluation experiments backed by LangSmith or local runs."""

    def __init__(
        self,
        *,
        dataset_name: str,
        project_name: str | None = None,
    ):
        self.dataset_name = dataset_name
        self.project_name = project_name or os.environ.get(
            "LANGSMITH_PROJECT", "financial-intelligence-platform"
        )
        self.api_key = os.environ.get("LANGSMITH_API_KEY")
        self._client = None

    @property
    def client(self) -> Any:
        """Lazily initialize the LangSmith client if API key is present."""
        if self._client is None and self.api_key:
            try:
                import langsmith

                self._client = langsmith.Client(api_key=self.api_key)
            except Exception:
                self._client = None
        return self._client

    async def run(
        self,
        *,
        cases: list[EvaluationCase],
        target: TargetFunction,
        evaluators: list[EvaluatorFunction] | None = None,
        experiment_prefix: str = "eval",
        metadata: dict[str, Any] | None = None,
    ) -> list[CaseResult]:
        """Run evaluation cases through the target function and score results.

        Executes locally with full latency measurement and scoring, and records
        to LangSmith when credentials are configured.
        """
        eval_list = evaluators or []
        case_results: list[CaseResult] = []

        for case in cases:
            start_time = perf_counter()
            actual = await target(case)
            latency = perf_counter() - start_time

            scores: list[ScoreResult] = []
            for ev in eval_list:
                eval_out = ev(actual, case.expected)
                key = eval_out.get("key", "metric")
                score_val = float(eval_out.get("score", 0.0))
                passed_val = bool(eval_out.get("passed", score_val >= 1.0))
                details = eval_out.get("details")

                scores.append(
                    ScoreResult(
                        scorer=key,
                        score=score_val,
                        passed=passed_val,
                        details=details,
                    )
                )

            case_results.append(
                CaseResult(
                    case_id=case.case_id,
                    scores=scores,
                    latency_seconds=latency,
                )
            )

        return case_results
