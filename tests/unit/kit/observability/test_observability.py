"""Unit tests for kit observability models, sanitization, and runner."""

import pytest

from kit.evaluation.models import EvaluationCase
from kit.observability.langsmith import LangSmithExperimentRunner
from kit.observability.models import TraceMetadata, sanitize_metadata


def test_sanitize_metadata_redacts_secrets():
    raw = {
        "user_id": "usr-123",
        "db_password": "super-secret-password",
        "api_key": "sk-1234567890",
        "nested": {
            "oauth_token": "bearer-token-val",
            "safe_field": 42,
        },
    }

    clean = sanitize_metadata(raw)

    assert clean["user_id"] == "usr-123"
    assert clean["db_password"] == "[REDACTED]"
    assert clean["api_key"] == "[REDACTED]"
    assert clean["nested"]["oauth_token"] == "[REDACTED]"
    assert clean["nested"]["safe_field"] == 42


def test_trace_metadata_to_runnable_config():
    trace = TraceMetadata(
        request_id="req-999",
        thread_id="thr-888",
        component="policy_agent",
        tags=["production"],
        metadata={"query_type": "high_value"},
    )

    cfg = trace.to_runnable_config(run_name="financial_policy_search")

    assert cfg["run_name"] == "financial_policy_search"
    assert cfg["configurable"]["thread_id"] == "thr-888"
    assert "production" in cfg["tags"]
    assert "policy_agent" in cfg["tags"]
    assert "request:req-999" in cfg["tags"]
    assert cfg["metadata"]["request_id"] == "req-999"
    assert cfg["metadata"]["thread_id"] == "thr-888"
    assert cfg["metadata"]["component"] == "policy_agent"
    assert cfg["metadata"]["query_type"] == "high_value"


@pytest.mark.anyio
async def test_langsmith_experiment_runner_offline_run():
    runner = LangSmithExperimentRunner(
        dataset_name="test-dataset",
        project_name="test-project",
    )

    cases = [
        EvaluationCase(
            case_id="TEST-001",
            category="risk",
            input={"amount": 500000},
            expected={"level": "high"},
        ),
        EvaluationCase(
            case_id="TEST-002",
            category="risk",
            input={"amount": 10000},
            expected={"level": "low"},
        ),
    ]

    async def mock_target(case: EvaluationCase) -> dict:
        amt = case.input["amount"]
        level = "high" if amt >= 400000 else "low"
        return {"level": level}

    def evaluate_level(actual: dict, expected: dict) -> dict:
        passed = actual.get("level") == expected.get("level")
        return {
            "key": "level_match",
            "score": 1.0 if passed else 0.0,
            "passed": passed,
        }

    results = await runner.run(
        cases=cases,
        target=mock_target,
        evaluators=[evaluate_level],
    )

    assert len(results) == 2
    assert results[0].case_id == "TEST-001"
    assert results[0].scores[0].passed is True
    assert results[0].scores[0].score == 1.0
    assert results[0].latency_seconds is not None
    assert results[0].latency_seconds >= 0.0

    assert results[1].case_id == "TEST-002"
    assert results[1].scores[0].passed is True
