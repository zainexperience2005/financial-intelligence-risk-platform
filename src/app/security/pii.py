"""Financial-domain PII classification and trust-boundary helpers."""

import json
from collections.abc import Mapping
from typing import Any

from kit.security.pii import PIIType, mask_mapping
from kit.security.redaction import redact_mapping

FINANCIAL_PII_FIELDS: dict[str, PIIType] = {
    "customer_name": PIIType.PERSON_NAME,
    "account_number": PIIType.ACCOUNT_NUMBER,
    "email": PIIType.EMAIL,
    "phone": PIIType.PHONE,
}


def mask_financial_data(data: Mapping[str, Any]) -> dict[str, Any]:
    """Return a model-safe copy using the financial PII field policy."""
    return mask_mapping(data, field_types=FINANCIAL_PII_FIELDS)


def prepare_model_evidence(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Remove secrets and classified PII immediately before model exposure."""
    redacted = redact_mapping(dict(evidence))
    return mask_financial_data(redacted)


def prepare_trace_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Prepare financial metadata for an AI tracing boundary."""
    return prepare_model_evidence(metadata)


def prepare_log_data(data: Mapping[str, Any]) -> dict[str, Any]:
    """Prepare structured financial data for ordinary application logs."""
    return prepare_model_evidence(data)


def prepare_model_text(value: Any) -> str:
    """Sanitize text or serialized structured data before model exposure."""
    if not isinstance(value, str):
        return json.dumps(
            prepare_model_evidence({"value": value})["value"], default=str
        )

    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        from kit.security.pii import mask_free_text

        return mask_free_text(value)

    safe_value = prepare_model_evidence({"value": parsed})["value"]
    return json.dumps(safe_value, default=str)
