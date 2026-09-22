from dataclasses import dataclass

from app.memory.builders import build_investigation_memory


@dataclass
class FakeRiskAssessment:
    score: int
    level: str
    ruleset_version: str


def test_build_investigation_memory_content_and_metadata():
    fake_risk = FakeRiskAssessment(
        score=90,
        level="high",
        ruleset_version="financial-risk-v1",
    )

    content, metadata = build_investigation_memory(
        transaction_id="TX-1006",
        risk_assessment=fake_risk,
        policy_sources=["FIN-POL-001", "FIN-POL-003"],
    )

    assert "Transaction TX-1006 was investigated" in content
    assert "score: 90" in content
    assert "level: high" in content
    assert "FIN-POL-001" in content
    assert "FIN-POL-003" in content

    assert metadata["transaction_id"] == "TX-1006"
    assert metadata["risk_score"] == "90"
    assert metadata["risk_level"] == "high"
    assert metadata["ruleset_version"] == "financial-risk-v1"
    assert metadata["policy_sources"] == "FIN-POL-001, FIN-POL-003"

    # Security verification: memory MUST NOT contain sensitive customer PII
    # or raw account balances
    forbidden_keys = {

        "customer_name",
        "account_id",
        "balance",
        "password",
        "ssn",
        "token",
        "sql_rows",
    }
    assert not forbidden_keys.intersection(metadata.keys())


def test_build_investigation_memory_empty_policy_sources():
    fake_risk = FakeRiskAssessment(
        score=20,
        level="low",
        ruleset_version="financial-risk-v1",
    )

    content, metadata = build_investigation_memory(
        transaction_id="TX-1001",
        risk_assessment=fake_risk,
        policy_sources=[],
    )

    assert "Policy sources: none" in content
    assert metadata["policy_sources"] == "none"
