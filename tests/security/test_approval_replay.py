"""Red-team security tests verifying approval replay protection."""

import pytest
from sqlalchemy import func, select

from app.actions.freeze_account import freeze_account
from app.audit.events import AuditEventType
from app.core.exceptions import ActionNotAllowedError
from app.db.models import ApprovalRecord, AuditEvent
from app.db.repositories.audit import find_by_event_type
from app.schemas import ProposedAction
from app.services.actions import ActionService
from app.services.approvals import approve_action, request_action_approval
from kit.databases.session import SessionFactory


def test_approval_cannot_be_replayed_sequentially(action_service: ActionService):
    """An approval transitioned to 'executed' must never be accepted a second time."""
    # 1. Propose & approve
    approval = request_action_approval(
        ProposedAction(
            action="freeze_account",
            account_id="ACC-1001",
            reason="Confirmed high-value fraud review.",
        )
    )
    approved = approve_action(
        approval_id=approval.approval_id,
        decided_by="compliance_lead@example.com",
        reason="Approved based on verified findings.",
    )
    approval_id = approved.approval_id

    # 2. First execution succeeds
    res1 = action_service.execute(
        action="freeze_account",
        account_id="ACC-1001",
        approval_id=approval_id,
        executed_by="analyst@example.com",
    )
    assert res1.success is True

    # Check status changed to executed
    with SessionFactory() as session:
        app_rec = session.scalar(
            select(ApprovalRecord).where(
                ApprovalRecord.approval_id == approved.approval_id
            )
        )
        assert app_rec.status == "executed"

    # 3. Second execution attempt MUST fail
    with pytest.raises(ActionNotAllowedError) as exc_info:
        action_service.execute(
            action="freeze_account",
            account_id="ACC-1001",
            approval_id=approval_id,
            executed_by="attacker@evil.corp",
        )
    assert "Action has not been approved" in str(exc_info.value)

    # 4. Verify only one successful action execution and denial audited
    with SessionFactory() as session:
        exec_count = session.scalar(
            select(func.count(AuditEvent.id)).where(
                AuditEvent.event_type == "action_executed"
            )
        )
        assert exec_count == 1

        denials = find_by_event_type(session, AuditEventType.ACTION_EXECUTION_DENIED)
        assert len(denials) >= 1
        assert denials[-1].details.get("reason_code") == "approval_already_executed"


def test_direct_freeze_account_fails_on_replayed_approval():
    """Direct invocation of freeze_account must reject executed approvals."""
    approval = request_action_approval(
        ProposedAction(
            action="freeze_account",
            account_id="ACC-1001",
            reason="High risk alert.",
        )
    )
    approved = approve_action(
        approval_id=approval.approval_id,
        decided_by="compliance@example.com",
    )
    approval_id = approved.approval_id

    # First call succeeds
    res1 = freeze_account(
        account_id="ACC-1001",
        approval_id=approval_id,
        actor="analyst@example.com",
    )
    assert res1.success is True

    # Replay call fails and is audited
    with pytest.raises(ActionNotAllowedError) as exc_info:
        freeze_account(
            account_id="ACC-1001",
            approval_id=approval_id,
            actor="replay_attacker@example.com",
        )
    assert "Action has not been approved" in str(exc_info.value)

    with SessionFactory() as session:
        denials = find_by_event_type(session, AuditEventType.ACTION_EXECUTION_DENIED)
        assert len(denials) >= 1
        assert denials[-1].details.get("reason_code") == "approval_already_executed"
