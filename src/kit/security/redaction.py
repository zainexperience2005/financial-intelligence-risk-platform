"""Security redaction utilities for scrubbing credentials and secrets from mappings."""

from typing import Any

SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "password",
    "secret",
    "token",
    "credentials",
    "database_url",
    "private_key",
}


def redact_mapping(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively scrub sensitive credential keys from a dictionary mapping."""
    result: dict[str, Any] = {}

    for key, value in data.items():
        normalized = key.lower()

        if any(sensitive in normalized for sensitive in SENSITIVE_KEYS):
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = redact_mapping(value)
        elif isinstance(value, list):
            result[key] = [
                redact_mapping(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result
