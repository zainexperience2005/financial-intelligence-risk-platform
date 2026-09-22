"""Red-team security tests verifying credential and secret leakage prevention."""

from kit.observability.models import sanitize_metadata
from kit.security.redaction import redact_mapping


def test_redact_mapping_scrubs_all_sensitive_keys():
    """Verify that credentials and secrets are reliably redacted from dictionaries."""
    data = {
        "account_id": "ACC-1001",
        "openai_api_key": "sk-proj-super-secret-key-12345",
        "db_password": "ProductionP@ssword99!",
        "auth_token": "bearer-jwt-token-abcdef",
        "database_url": "postgresql://admin:secret@prod-db:5432/finance",
        "public_flag": True,
    }

    cleaned = redact_mapping(data)

    assert cleaned["account_id"] == "ACC-1001"
    assert cleaned["public_flag"] is True
    assert cleaned["openai_api_key"] == "[REDACTED]"
    assert cleaned["db_password"] == "[REDACTED]"
    assert cleaned["auth_token"] == "[REDACTED]"
    assert cleaned["database_url"] == "[REDACTED]"


def test_redact_mapping_recurses_into_nested_structures():
    """Verify recursive scrubbing across nested dictionaries and list elements."""
    payload = {
        "headers": {
            "Authorization": "Bearer confidential_token",
            "Content-Type": "application/json",
        },
        "records": [
            {"service": "qdrant", "api_key": "secret-qdrant-key"},
            {"service": "postgres", "safe_name": "financial_reader"},
        ],
    }

    cleaned = redact_mapping(payload)

    assert cleaned["headers"]["Authorization"] == "[REDACTED]"
    assert cleaned["headers"]["Content-Type"] == "application/json"
    assert cleaned["records"][0]["api_key"] == "[REDACTED]"
    assert cleaned["records"][1]["safe_name"] == "financial_reader"


def test_observability_metadata_sanitization():
    """Verify trace metadata prevents credentials from leaking to platforms."""
    raw_meta = {
        "caller": "api_gateway",
        "internal_secret": "my-secret-vault-token",
        "query": "SELECT * FROM accounts",
    }

    sanitized = sanitize_metadata(raw_meta)

    assert sanitized["caller"] == "api_gateway"
    assert sanitized["internal_secret"] == "[REDACTED]"
    assert sanitized["query"] == "SELECT * FROM accounts"
