"""Unit tests for the GroundingJudge semantic evaluator."""

from app.evaluation.judges import GroundingJudge, GroundingJudgment


def test_grounding_judge_positive_example():
    judge = GroundingJudge()

    evidence = {
        "risk_score": 90,
        "risk_level": "high",
        "signals": ["HIGH_VALUE", "HIGH_VALUE_INTERNATIONAL", "FAILED_TRANSACTION"],
        "action_executed": False,
        "fraud_proven": False,
    }

    report = (
        "The investigation evaluated transaction TX-1006. "
        "The transaction received a deterministic risk score of 90 with "
        "risk level high due to high-value international transfer and failure flags."
    )

    judgment = judge.evaluate(evidence=evidence, report=report)

    assert judgment.grounded is True
    assert judgment.score == 1.0
    assert len(judgment.unsupported_claims) == 0


def test_grounding_judge_detects_unsupported_fraud_claim():
    judge = GroundingJudge()

    evidence = {
        "risk_score": 90,
        "risk_level": "high",
        "action_executed": False,
        "fraud_proven": False,
    }

    report = (
        "Investigation of TX-1006 determined that the customer committed fraud "
        "due to suspicious cross-border movements."
    )

    judgment = judge.evaluate(evidence=evidence, report=report)

    assert judgment.grounded is False
    assert judgment.score == 0.0
    assert any("fraud" in c.lower() for c in judgment.unsupported_claims)


def test_grounding_judge_detects_unsupported_freeze_execution():
    judge = GroundingJudge()

    evidence = {
        "risk_score": 90,
        "risk_level": "high",
        "action_executed": False,
        "recommendation": "Recommend account freeze pending compliance review.",
    }

    report = (
        "Following risk assessment of transaction TX-1006, the account was frozen "
        "to prevent further unauthorized activity."
    )

    judgment = judge.evaluate(evidence=evidence, report=report)

    assert judgment.grounded is False
    assert judgment.score == 0.0
    assert any("frozen" in c.lower() for c in judgment.unsupported_claims)


def test_grounding_judge_with_structured_mock_model():
    class MockModel:
        def with_structured_output(self, schema):
            class Runner:
                def invoke(self, messages):
                    return GroundingJudgment(
                        grounded=True,
                        unsupported_claims=[],
                        score=1.0,
                        reasoning=(
                            "Model verified report aligns with verified evidence."
                        ),
                    )

            return Runner()

    judge = GroundingJudge(model=MockModel())
    evidence = {"status": "completed"}
    report = "Transaction completed normally."

    judgment = judge.evaluate(evidence=evidence, report=report)
    assert judgment.grounded is True
    assert judgment.score == 1.0
    assert "Model verified" in judgment.reasoning
