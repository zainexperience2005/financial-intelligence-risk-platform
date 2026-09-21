import pytest
from pydantic import ValidationError

from app.schemas import FinancialAnalysis


def test_financial_analysis_valid() -> None:
    analysis = FinancialAnalysis(
        summary="Failure rate increased.",
        reasoning="More transactions failed.",
        confidence="medium",
        requires_data=True,
    )

    assert analysis.requires_data is True
    assert analysis.confidence == "medium"


def test_financial_analysis_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        FinancialAnalysis(
            summary="Test",
            reasoning="Test",
            confidence="certain",
            requires_data=False,
        )