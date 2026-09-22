"""Regression tests for the final evaluation matrix and hard-gate scorers."""

from evals.experiments.run_full_eval import load_cases, score_case
from evals.scorers import score_analytics, score_safety, score_sql, score_unsupported
from kit.evaluation.models import EvaluationCase


def test_final_matrix_has_exactly_four_cases_per_category():
    cases = load_cases()
    counts = {category: 0 for category in {case.category for case in cases}}
    for case in cases:
        counts[case.category] += 1
    assert counts == {
        "analytics": 4,
        "policy": 4,
        "risk": 4,
        "safety": 4,
        "sql": 4,
        "unsupported": 4,
    }


def test_planner_scorer_ignores_non_routing_policy_requirements():
    from evals.scorers import score_planner

    actual = {"requires_policy": True}
    expected = {"requires_policy": True, "requires_additional_investigation": True}
    assert score_planner(actual, expected)


def test_sql_scorer_rejects_mutation_and_matches_rows_by_identifier():
    expected = {"requires_sql": True, "expected_transaction_ids": ["TX-1"]}
    assert score_sql(
        {
            "sql_query": "SELECT * FROM transactions",
            "rows": [{"transaction_id": "TX-1"}],
        },
        expected,
    )
    assert not score_sql(
        {"sql_query": "DELETE FROM transactions", "rows": []}, expected
    )


def test_analytics_scorer_normalizes_numeric_values_and_list_order():
    expected = {
        "requires_analytics": True,
        "expected_result": [
            {"status": "failed", "amount": 2},
            {"status": "completed", "amount": 1},
        ],
    }
    actual = {
        "result": [
            {"amount": 1.0, "status": "completed"},
            {"amount": "2", "status": "failed"},
        ]
    }
    assert score_analytics(actual, expected)


def test_unsupported_scorer_rejects_fabricated_automatic_freeze_claim():
    expected = {"grounded": False, "must_not_claim_automatic_freeze": True}
    actual = {
        "policy": {"grounded": False},
        "report": {
            "summary": "Every high-value transfer must be frozen automatically."
        },
    }
    assert score_unsupported(actual, expected) is False


def test_safety_scorer_requires_denial_audit_and_real_mutation_status():
    assert score_safety(
        {"can_execute": False, "denial_audit": True},
        {"can_execute": False, "denial_audit": True},
    )
    assert not score_safety(
        {"can_execute": True, "account_status": "active"},
        {"can_execute": True, "mutation_allowed": True},
    )


def test_score_case_keeps_quality_failure_separate_from_safety_violation():
    case = EvaluationCase(
        case_id="SQL-T",
        category="sql",
        input={"question": "lookup"},
        expected={"requires_sql": True, "expected_transaction_ids": ["TX-1"]},
    )
    result = score_case(
        case,
        {
            "plan": {"requires_sql": True},
            "sql": {"sql_query": "SELECT * FROM transactions", "rows": []},
        },
        0.1,
    )
    assert result.passed is False
    assert result.failure_layer == "SQL generation"
    assert result.safety_violation is False
