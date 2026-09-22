from app.memory.policy import should_store_investigation


def test_completed_transaction_investigation_is_stored():
    decision = should_store_investigation(
        transaction_id="TX-1006",
        report_available=True,
        risk_available=True,
    )

    assert decision.should_store is True
    assert decision.reason == "Completed transaction investigation."


def test_general_question_is_not_stored():
    decision = should_store_investigation(
        transaction_id=None,
        report_available=True,
        risk_available=False,
    )

    assert decision.should_store is False
    assert "No transaction-specific" in decision.reason


def test_missing_report_is_not_stored():
    decision = should_store_investigation(
        transaction_id="TX-1006",
        report_available=False,
        risk_available=True,
    )

    assert decision.should_store is False
    assert "No completed report" in decision.reason


def test_missing_risk_is_not_stored():
    decision = should_store_investigation(
        transaction_id="TX-1006",
        report_available=True,
        risk_available=False,
    )

    assert decision.should_store is False
    assert "No deterministic risk assessment" in decision.reason
