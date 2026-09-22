"""Regression tests for application PII trust boundaries."""

from app.security.pii import (
    prepare_log_data,
    prepare_model_evidence,
    prepare_trace_metadata,
)
from kit.observability.models import TraceMetadata

RAW_EVIDENCE = {
    "customer_name": "Ali Khan",
    "email": "ali@example.com",
    "phone": "+92 300 1234567",
    "account_number": "PK-10004567",
    "amount": 475000,
    "transaction_id": "TX-1006",
    "nested": [{"email_address": "sara@example.com"}],
}


def _assert_safe(data: dict) -> None:
    serialized = str(data)
    for pii in (
        "Ali Khan",
        "ali@example.com",
        "+92 300 1234567",
        "PK-10004567",
        "sara@example.com",
    ):
        assert pii not in serialized
    assert "TX-1006" in serialized
    assert "475000" in serialized


def test_model_context_does_not_contain_customer_pii() -> None:
    _assert_safe(prepare_model_evidence(RAW_EVIDENCE))


def test_trace_metadata_does_not_contain_customer_pii() -> None:
    _assert_safe(prepare_trace_metadata(RAW_EVIDENCE))
    config = TraceMetadata(metadata=RAW_EVIDENCE).to_runnable_config()
    _assert_safe(config["metadata"])


def test_log_data_does_not_contain_customer_pii() -> None:
    _assert_safe(prepare_log_data(RAW_EVIDENCE))


def test_report_prompt_does_not_contain_customer_pii() -> None:
    from unittest.mock import MagicMock, patch

    from app.agents.report_agent import create_investigation_report
    from app.schemas import InvestigationReport

    model = MagicMock()
    model.with_structured_output.return_value = model
    model.invoke.return_value = InvestigationReport(
        executive_summary="Masked evidence was assessed.",
        evidence_sufficient=True,
    )

    with patch("app.agents.report_agent.create_chat_model", return_value=model):
        create_investigation_report(RAW_EVIDENCE)

    prompt = model.invoke.call_args.args[0][1].content
    assert "Ali Khan" not in prompt
    assert "ali@example.com" not in prompt
    assert "+92 300 1234567" not in prompt
    assert "PK-10004567" not in prompt
    assert "TX-1006" in prompt
    assert "475000" in prompt
