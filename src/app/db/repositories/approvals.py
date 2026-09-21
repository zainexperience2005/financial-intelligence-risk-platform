from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ApprovalRecord


def create_approval(
    session: Session,
    *,
    approval_id: str,
    action: str,
    arguments: dict[str, Any],
    reason: str,
) -> ApprovalRecord:
    """Creates a new pending approval record in the database."""
    record = ApprovalRecord(
        approval_id=approval_id,
        action=action,
        arguments=arguments,
        reason=reason,
        status="pending",
        created_at=datetime.now(UTC),
    )

    session.add(record)

    return record


def get_approval(
    session: Session,
    approval_id: str,
) -> ApprovalRecord | None:
    """Retrieves an approval record by its unique approval ID."""
    statement = select(ApprovalRecord).where(ApprovalRecord.approval_id == approval_id)

    return session.scalar(statement)


def approve_record(
    record: ApprovalRecord,
    *,
    decided_by: str,
    reason: str | None,
) -> None:
    """Transitions a pending approval record to approved status."""
    if record.status != "pending":
        raise ValueError("Approval request has already been decided.")

    record.status = "approved"
    record.decided_by = decided_by
    record.decision_reason = reason
    record.decided_at = datetime.now(UTC)


def reject_record(
    record: ApprovalRecord,
    *,
    decided_by: str,
    reason: str | None,
) -> None:
    """Transitions a pending approval record to rejected status."""
    if record.status != "pending":
        raise ValueError("Approval request has already been decided.")

    record.status = "rejected"
    record.decided_by = decided_by
    record.decision_reason = reason
    record.decided_at = datetime.now(UTC)


def mark_approval_executed(
    record: ApprovalRecord,
) -> None:
    """Marks an approved request as executed to prevent approval replay."""
    if record.status != "approved":
        raise ValueError("Approval is not executable.")

    record.status = "executed"
    record.executed_at = datetime.now(UTC)
