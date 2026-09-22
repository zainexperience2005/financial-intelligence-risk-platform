"""Data models for evaluation cases, score results, and reports."""

from typing import Any

from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    """Represents a single golden evaluation case."""

    case_id: str
    category: str
    input: dict[str, Any]
    expected: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScoreResult(BaseModel):
    """Result of evaluating an actual output against an expectation."""

    scorer: str
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    details: str | None = None


class CaseResult(BaseModel):
    """Evaluation outcomes for an individual test case."""

    case_id: str
    scores: list[ScoreResult]
    latency_seconds: float | None = None
    token_count: int | None = None
    estimated_cost_usd: float | None = None


class EvaluationReport(BaseModel):
    """Aggregated evaluation report across multiple cases."""

    results: list[CaseResult]

    @property
    def total_cases(self) -> int:
        """Total number of evaluated cases."""
        return len(self.results)

    @property
    def all_passed(self) -> bool:
        """True if all scorers across all cases passed."""
        return all(s.passed for res in self.results for s in res.scores)
