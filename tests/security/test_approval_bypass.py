"""Red-team security tests verifying that actions cannot bypass the approval gate."""

import pytest
from sqlalchemy import select

from app.actions.freeze_account import freeze_account
from app.core.exceptions import ActionNotAllowedError
from app.db.models import Account
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

    # Verify directly via freeze_account
    direct_res = freeze_account(
        account_id="ACC-1001",
        approval_id="fake-approval-uuid-666",
        actor="attacker@evil.corp",
    )
    assert direct_res.success is False

    # Verify database state was not modified
    with SessionFactory() as session:
        acc = session.scalar(select(Account).where(Account.account_id == "ACC-1001"))
        assert acc is not None
        assert acc.status == "active"


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

    # Verify database state
    with SessionFactory() as session:
        acc = session.scalar(select(Account).where(Account.account_id == "ACC-1001"))
        assert acc is not None
        assert acc.status == "active"


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
