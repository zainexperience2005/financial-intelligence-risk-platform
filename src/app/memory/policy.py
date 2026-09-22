from pydantic import BaseModel

INVESTIGATION_MEMORY_RETENTION_DAYS = 30


class MemoryPersistenceDecision(BaseModel):
    should_store: bool
    reason: str


def should_store_investigation(
    *,
    transaction_id: str | None,
    report_available: bool,
    risk_available: bool,
) -> MemoryPersistenceDecision:
    """Determines whether an investigation is eligible for long-term memory."""

    if not transaction_id:
        return MemoryPersistenceDecision(
            should_store=False,
            reason="No transaction-specific investigation.",
        )

    if not report_available:
        return MemoryPersistenceDecision(
            should_store=False,
            reason="No completed report.",
        )

    if not risk_available:
        return MemoryPersistenceDecision(
            should_store=False,
            reason="No deterministic risk assessment available.",
        )

    return MemoryPersistenceDecision(
        should_store=True,
        reason="Completed transaction investigation.",
    )
