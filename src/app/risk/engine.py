from decimal import Decimal

from app.risk.models import (
    RiskAssessment,
    RiskSignal,
)

HIGH_VALUE_THRESHOLD = Decimal("400000")
INTERNATIONAL_THRESHOLD = Decimal("300000")


def assess_transaction_risk(
    *,
    amount: Decimal,
    status: str,
    failure_reason: str | None,
    destination_country: str | None,
    customer_country: str | None,
) -> RiskAssessment:
    signals: list[RiskSignal] = []

    if amount >= HIGH_VALUE_THRESHOLD:
        signals.append(
            RiskSignal(
                code="HIGH_VALUE",
                description=("Transaction amount is at least PKR 400,000."),
                points=30,
            )
        )

    is_international = (
        destination_country is not None
        and customer_country is not None
        and destination_country.lower() != customer_country.lower()
    )

    if is_international and amount >= INTERNATIONAL_THRESHOLD:
        signals.append(
            RiskSignal(
                code="HIGH_VALUE_INTERNATIONAL",
                description=(
                    "International transaction amount is at least PKR 300,000."
                ),
                points=25,
            )
        )

    if status.lower() == "failed":
        signals.append(
            RiskSignal(
                code="FAILED_TRANSACTION",
                description=("Transaction status is failed."),
                points=10,
            )
        )

    if failure_reason and failure_reason.lower() == "risk_review":
        signals.append(
            RiskSignal(
                code="RISK_REVIEW_FAILURE",
                description=("Transaction failed because of risk review."),
                points=25,
            )
        )

    raw_score = sum(signal.points for signal in signals)

    score = min(raw_score, 100)

    if score >= 70:
        level = "high"
    elif score >= 40:
        level = "medium"
    else:
        level = "low"

    return RiskAssessment(
        score=score,
        level=level,
        signals=signals,
    )
