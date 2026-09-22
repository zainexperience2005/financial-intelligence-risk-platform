"""Unit tests for reusable PII masking."""

from kit.security.pii import (
    PIIMaskingPolicy,
    PIIType,
    mask_free_text,
    mask_mapping,
)


def test_masks_email() -> None:
    masked = mask_free_text("Contact ali@example.com")
    assert "ali@example.com" not in masked
    assert "[EMAIL]" in masked


def test_masks_phone() -> None:
    masked = mask_free_text("Phone: +92 300 1234567")
    assert "+92 300 1234567" not in masked
    assert "[PHONE]" in masked


def test_masks_structured_pii_without_mutating_input() -> None:
    data = {
        "customer_name": "Ali Khan",
        "email": "ali@example.com",
        "amount": 475000,
        "transaction_id": "TX-1006",
    }
    masked = mask_mapping(data)

    assert masked["customer_name"] == "[PERSON_NAME]"
    assert masked["email"] == "[EMAIL]"
    assert masked["amount"] == 475000
    assert masked["transaction_id"] == "TX-1006"
    assert data["customer_name"] == "Ali Khan"


def test_masks_nested_pii() -> None:
    masked = mask_mapping(
        {
            "transaction": {
                "transaction_id": "TX-1006",
                "customer": {
                    "customer_name": "Ali Khan",
                    "email": "ali@example.com",
                },
            }
        }
    )
    customer = masked["transaction"]["customer"]
    assert customer["customer_name"] == "[PERSON_NAME]"
    assert customer["email"] == "[EMAIL]"


def test_masks_lists() -> None:
    masked = mask_mapping(
        {
            "customers": [
                {"customer_name": "Ali Khan", "email": "ali@example.com"},
                {"customer_name": "Sara Ahmed", "email": "sara@example.com"},
            ]
        }
    )
    for customer in masked["customers"]:
        assert customer["customer_name"] == "[PERSON_NAME]"
        assert customer["email"] == "[EMAIL]"


def test_preserves_non_pii_financial_evidence() -> None:
    data = {
        "transaction_id": "TX-1006",
        "amount": 475000,
        "status": "failed",
        "risk_score": 90,
        "risk_level": "high",
    }
    assert mask_mapping(data) == data


def test_policy_can_leave_unselected_type_unmasked() -> None:
    policy = PIIMaskingPolicy(masked_types=frozenset({PIIType.EMAIL}))
    masked = mask_mapping(
        {"email": "ali@example.com", "phone": "+92 300 1234567"},
        policy=policy,
    )
    assert masked["email"] == "[EMAIL]"
    assert masked["phone"] == "+92 300 1234567"
