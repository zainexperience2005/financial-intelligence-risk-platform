from decimal import Decimal

from app.risk.engine import (
    assess_transaction_risk,
)


def test_low_risk_transaction() -> None:
    result = assess_transaction_risk(
        amount=Decimal("10000"),
        status="completed",
        failure_reason=None,
        destination_country="Pakistan",
        customer_country="Pakistan",
    )

    assert result.score == 0
    assert result.level == "low"
    assert result.signals == []


def test_high_value_transaction() -> None:
    result = assess_transaction_risk(
        amount=Decimal("450000"),
        status="completed",
        failure_reason=None,
        destination_country="Pakistan",
        customer_country="Pakistan",
    )

    assert result.score == 30
    assert result.level == "low"

    assert any(signal.code == "HIGH_VALUE" for signal in result.signals)


def test_high_risk_transaction() -> None:
    result = assess_transaction_risk(
        amount=Decimal("475000"),
        status="failed",
        failure_reason="risk_review",
        destination_country="UAE",
        customer_country="Pakistan",
    )

    assert result.score == 90
    assert result.level == "high"

    codes = {signal.code for signal in result.signals}

    assert codes == {
        "HIGH_VALUE",
        "HIGH_VALUE_INTERNATIONAL",
        "FAILED_TRANSACTION",
        "RISK_REVIEW_FAILURE",
    }
