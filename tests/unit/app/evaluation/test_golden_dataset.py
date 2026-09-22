"""Unit tests for the financial golden evaluation dataset and scorers."""

import json
from decimal import Decimal
from pathlib import Path

from app.evaluation.scorers import (
    score_expected_sources,
    score_risk_assessment,
    score_unsupported_grounding,
)
from app.risk.engine import assess_transaction_risk
from kit.evaluation.models import EvaluationCase
from kit.evaluation.scorers import exact_match, numeric_match

DATASET_PATH = Path("evals/datasets/financial_golden.json")


def load_dataset() -> list[dict]:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def test_golden_dataset_has_at_least_20_cases():
    cases = load_dataset()
    assert len(cases) >= 20, f"Expected at least 20 cases, found {len(cases)}"


def test_case_ids_are_unique():
    cases = load_dataset()
    ids = [c["case_id"] for c in cases]
    assert len(ids) == len(set(ids)), f"Duplicate case IDs found: {ids}"


def test_all_cases_validate_schema():
    cases = load_dataset()
    for raw in cases:
        parsed = EvaluationCase.model_validate(raw)
        assert parsed.case_id
        assert parsed.category
        assert isinstance(parsed.input, dict)
        assert isinstance(parsed.expected, dict)


def test_categories_covered():
    cases = load_dataset()
    categories = {c["category"] for c in cases}
    expected_categories = {
        "sql",
        "analytics",
        "policy",
        "risk",
        "unsupported",
        "safety",
    }
    missing = expected_categories - categories
    assert expected_categories.issubset(categories), f"Missing categories: {missing}"


def test_deterministic_risk_cases_pass():
    cases = [c for c in load_dataset() if c["category"] == "risk"]
    assert len(cases) == 4

    for case in cases:
        tx = case["input"]["transaction"]
        actual = assess_transaction_risk(
            amount=Decimal(str(tx["amount"])),
            status=str(tx["status"]),
            failure_reason=tx.get("failure_reason"),
            destination_country=tx.get("destination_country"),
            customer_country=case["input"]["customer_country"],
        )

        scores = score_risk_assessment(
            actual=actual,
            expected_score=case["expected"]["risk_score"],
            expected_level=case["expected"]["risk_level"],
            expected_signals=case["expected"].get("expected_signals"),
        )

        assert all(s.passed for s in scores), f"Case {case['case_id']} failed: {scores}"


def test_exact_match_scorer():
    res_pass = exact_match(name="test_str", actual="high", expected="high")
    assert res_pass.passed is True
    assert res_pass.score == 1.0

    res_fail = exact_match(name="test_str", actual="low", expected="high")
    assert res_fail.passed is False
    assert res_fail.score == 0.0
    assert "Expected 'high', received 'low'" in res_fail.details


def test_numeric_match_scorer():
    res_pass = numeric_match(name="test_num", actual=90.0, expected=90.0, tolerance=0.0)
    assert res_pass.passed is True
    assert res_pass.score == 1.0

    res_tol = numeric_match(name="test_num", actual=90.05, expected=90.0, tolerance=0.1)
    assert res_tol.passed is True
    assert res_tol.score == 1.0

    res_fail = numeric_match(name="test_num", actual=90.2, expected=90.0, tolerance=0.1)
    assert res_fail.passed is False
    assert res_fail.score == 0.0


def test_score_expected_sources():
    res = score_expected_sources(
        actual_sources=["FIN-POL-001", "FIN-POL-002"],
        expected_sources=["FIN-POL-001"],
    )
    assert res.passed is True
    assert res.score == 1.0

    res_partial = score_expected_sources(
        actual_sources=["FIN-POL-001"],
        expected_sources=["FIN-POL-001", "FIN-POL-002"],
    )
    assert res_partial.passed is False
    assert res_partial.score == 0.5


def test_score_unsupported_grounding():
    res_correct = score_unsupported_grounding(grounded=False, expected_grounded=False)
    assert res_correct.passed is True
    assert res_correct.score == 1.0

    res_wrong = score_unsupported_grounding(grounded=True, expected_grounded=False)
    assert res_wrong.passed is False
    assert res_wrong.score == 0.0
