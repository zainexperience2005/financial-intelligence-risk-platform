"""Reusable deterministic PII masking at external trust boundaries."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PIIType(StrEnum):
    EMAIL = "email"
    PHONE = "phone"
    PERSON_NAME = "person_name"
    ACCOUNT_NUMBER = "account_number"


@dataclass(frozen=True)
class PIIMaskingPolicy:
    """Select the PII categories masked at a particular trust boundary."""

    masked_types: frozenset[PIIType] = field(default_factory=lambda: frozenset(PIIType))


EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"(?<!\w)\+?\d[\d\s\-()]{7,}\d(?!\w)")

DEFAULT_FIELD_TYPES: dict[str, PIIType] = {
    "name": PIIType.PERSON_NAME,
    "full_name": PIIType.PERSON_NAME,
    "customer_name": PIIType.PERSON_NAME,
    "email": PIIType.EMAIL,
    "email_address": PIIType.EMAIL,
    "phone": PIIType.PHONE,
    "phone_number": PIIType.PHONE,
    "account_number": PIIType.ACCOUNT_NUMBER,
}


def _placeholder(pii_type: PIIType) -> str:
    return f"[{pii_type.value.upper()}]"


def mask_free_text(
    value: str,
    *,
    policy: PIIMaskingPolicy | None = None,
) -> str:
    """Mask structurally recognizable email and phone values in free text."""
    active_policy = policy or PIIMaskingPolicy()
    masked = value
    if PIIType.EMAIL in active_policy.masked_types:
        masked = EMAIL_PATTERN.sub(_placeholder(PIIType.EMAIL), masked)
    if PIIType.PHONE in active_policy.masked_types:
        masked = PHONE_PATTERN.sub(_placeholder(PIIType.PHONE), masked)
    return masked


def mask_mapping(
    data: Mapping[str, Any],
    *,
    field_types: Mapping[str, PIIType] | None = None,
    policy: PIIMaskingPolicy | None = None,
) -> dict[str, Any]:
    """Return a recursively masked copy without changing authoritative input."""
    active_policy = policy or PIIMaskingPolicy()
    types = {**DEFAULT_FIELD_TYPES, **(field_types or {})}
    masked: dict[str, Any] = {}

    for key, value in data.items():
        pii_type = types.get(str(key).lower())
        if pii_type is not None and pii_type in active_policy.masked_types:
            masked[key] = _placeholder(pii_type)
        else:
            masked[key] = _mask_value(
                value,
                field_types=types,
                policy=active_policy,
            )

    return masked


def _mask_value(
    value: Any,
    *,
    field_types: Mapping[str, PIIType],
    policy: PIIMaskingPolicy,
) -> Any:
    if isinstance(value, Mapping):
        return mask_mapping(value, field_types=field_types, policy=policy)
    if isinstance(value, list):
        return [
            _mask_value(item, field_types=field_types, policy=policy) for item in value
        ]
    if isinstance(value, tuple):
        return tuple(
            _mask_value(item, field_types=field_types, policy=policy) for item in value
        )
    if isinstance(value, str):
        return mask_free_text(value, policy=policy)
    return value
