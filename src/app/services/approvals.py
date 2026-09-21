from uuid import uuid4

from app.db.models import ApprovalRecord
from app.db.repositories.approvals import (
    approve_record,
    create_approval,
    get_approval,
    reject_record,
)
from app.db.repositories.audit import (
    record_audit_event,
)
from app.schemas import ProposedAction
from kit.databases.session import (
    SessionFactory,
)


def request_action_approval(
    action: ProposedAction,
) -> ApprovalRecord:
    """Proposes a protected customer action and records an audit event in PostgreSQL."""
    approval_id = str(uuid4())

    with SessionFactory() as session:
        record = create_approval(
            session,
            approval_id=approval_id,
            action=action.action,
            arguments={
                "account_id": action.account_id,
            },
            reason=action.reason,
        )

        record_audit_event(
            session,
            event_type="approval_requested",
            actor="system",
            entity_type="approval",
            entity_id=approval_id,
            details={
                "action": action.action,
                "arguments": {
                    "account_id": action.account_id,
                },
            },
        )

        session.commit()
        session.refresh(record)

        return record


def approve_action(
    *,
    approval_id: str,
    decided_by: str,
    reason: str | None = None,
) -> ApprovalRecord:
    """Approve a pending action request and audit it within one transaction."""
    with SessionFactory() as session:
        record = get_approval(
            session,
            approval_id,
        )

        if record is None:
            raise ValueError("Approval request not found.")

        approve_record(
            record,
            decided_by=decided_by,
            reason=reason,
        )

        record_audit_event(
            session,
            event_type="approval_approved",
            actor=decided_by,
            entity_type="approval",
            entity_id=approval_id,
            details={
                "reason": reason,
            },
        )

        session.commit()
        session.refresh(record)

        return record


def reject_action(
    *,
    approval_id: str,
    decided_by: str,
    reason: str | None = None,
) -> ApprovalRecord:
    """Reject a pending action request and audit it within one transaction."""
    with SessionFactory() as session:
        record = get_approval(
            session,
            approval_id,
        )

        if record is None:
            raise ValueError("Approval request not found.")

        reject_record(
            record,
            decided_by=decided_by,
            reason=reason,
        )

        record_audit_event(
            session,
            event_type="approval_rejected",
            actor=decided_by,
            entity_type="approval",
            entity_id=approval_id,
            details={
                "reason": reason,
            },
        )

        session.commit()
        session.refresh(record)

        return record


def get_action_approval(
    approval_id: str,
) -> ApprovalRecord | None:
    """Retrieves an approval record from PostgreSQL."""
    with SessionFactory() as session:
        return get_approval(
            session,
            approval_id,
        )
