"""Typed result contracts for the final financial evaluation."""

from typing import Any

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    case_id: str
    category: str
    passed: bool
    planner_correct: bool | None = None
    sql_correct: bool | None = None
    analytics_correct: bool | None = None
    chart_correct: bool | None = None
    policy_source_correct: bool | None = None
    risk_correct: bool | None = None
    grounded: bool | None = None
    safety_violation: bool = False
    latency_seconds: float = Field(ge=0.0)
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    expected: dict[str, Any] = Field(default_factory=dict)
    actual: dict[str, Any] = Field(default_factory=dict)
    failure_layer: str | None = None
    likely_cause: str | None = None


class ExperimentMetadata(BaseModel):
    experiment_id: str
    dataset_version: str
    git_sha: str | None
    llm_provider: str
    llm_model: str
    risk_ruleset_version: str
    rag_mode: str
    started_at: str
