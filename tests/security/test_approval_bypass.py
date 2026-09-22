"""Red-team security tests verifying that actions cannot bypass the approval gate."""

import pytest
from sqlalchemy import select

from app.actions.freeze_account import freeze_account
from app.audit.events import AuditEventType
from app.core.exceptions import ActionNotAllowedError
from app.db.models import Account
from app.db.repositories.audit import find_by_event_type
from app.schemas import ProposedAction
from app.services.actions import ActionService
from app.services.approvals import reject_action, request_action_approval
from kit.databases.session import SessionFactory


def test_freeze_without_approval_fails(action_service: ActionService):
    """Execution with a fabricated approval ID must raise ActionNotAllowedError."""
    with pytest.raises(ActionNotAllowedError) as exc_info:
        action_service.execute(
            action="freeze_account",
            account_id="ACC-1001",
            approval_id="fake-approval-uuid-666",
            executed_by="attacker@evil.corp",
        )
    assert "Valid approval is required" in str(exc_info.value)

    # Verify directly via freeze_account raises ActionNotAllowedError
    with pytest.raises(ActionNotAllowedError):
        freeze_account(
            account_id="ACC-1001",
            approval_id="fake-approval-uuid-666",
            actor="attacker@evil.corp",
        )

    # Verify database state was not modified and denial was audited
    with SessionFactory() as session:
        acc = session.scalar(select(Account).where(Account.account_id == "ACC-1001"))
        assert acc is not None
        assert acc.status == "active"

        denials = find_by_event_type(session, AuditEventType.ACTION_EXECUTION_DENIED)
        assert len(denials) >= 2
        assert denials[-1].details.get("reason_code") == "approval_not_found"
        assert denials[-1].details.get("action") == "freeze_account"


def test_pending_approval_cannot_execute(action_service: ActionService):
    """An approval in 'pending' status must never authorize execution."""
    approval = request_action_approval(
        ProposedAction(
            action="freeze_account",
            account_id="ACC-1001",
            reason="Suspected high-risk transaction.",
        )
    )
    assert approval.status == "pending"

    with pytest.raises(ActionNotAllowedError) as exc_info:
        action_service.execute(
            action="freeze_account",
            account_id="ACC-1001",
            approval_id=approval.approval_id,
            executed_by="analyst@example.com",
        )
    assert "Action has not been approved" in str(exc_info.value)

    # Verify database state and denial audit
    with SessionFactory() as session:
        acc = session.scalar(select(Account).where(Account.account_id == "ACC-1001"))
        assert acc is not None
        assert acc.status == "active"

        denials = find_by_event_type(session, AuditEventType.ACTION_EXECUTION_DENIED)
        assert len(denials) >= 1
        assert denials[-1].details.get("reason_code") == "approval_pending"


def test_rejected_approval_cannot_execute(action_service: ActionService):
    """A rejected approval must never authorize execution."""
    approval = request_action_approval(
        ProposedAction(
            action="freeze_account",
            account_id="ACC-1001",
            reason="Suspected high-risk transaction.",
        )
    )
    reject_action(
        approval_id=approval.approval_id,
        decided_by="compliance_officer@example.com",
        reason="False positive alert.",
    )

    with pytest.raises(ActionNotAllowedError) as exc_info:
        action_service.execute(
            action="freeze_account",
            account_id="ACC-1001",
            approval_id=approval.approval_id,
            executed_by="analyst@example.com",
        )
    assert "Action has not been approved" in str(exc_info.value)

    with SessionFactory() as session:
        acc = session.scalar(select(Account).where(Account.account_id == "ACC-1001"))
        assert acc is not None
        assert acc.status == "active"

        denials = find_by_event_type(session, AuditEventType.ACTION_EXECUTION_DENIED)
        assert len(denials) >= 1
        assert denials[-1].details.get("reason_code") == "approval_rejected"
