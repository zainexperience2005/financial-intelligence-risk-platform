"""Red-team security tests verifying argument binding and substitution rejection."""

import pytest
from sqlalchemy import select

from app.actions.freeze_account import freeze_account
from app.audit.events import AuditEventType
from app.core.exceptions import ActionNotAllowedError
from app.db.models import Account
from app.db.repositories.audit import find_by_event_type
from app.schemas import ProposedAction
from app.services.actions import ActionService
from app.services.approvals import approve_action, request_action_approval
from kit.databases.session import SessionFactory


def test_approval_account_substitution_fails(action_service: ActionService):
    """Approval granted for ACC-1001 must be rejected if executed against ACC-9999."""
    # 1. Propose & approve for ACC-1001
    approval = request_action_approval(
        ProposedAction(
            action="freeze_account",
            account_id="ACC-1001",
            reason="High risk alert on account 1001.",
        )
    )
    approved = approve_action(
        approval_id=approval.approval_id,
        decided_by="compliance_officer@example.com",
    )
    approval_id = approved.approval_id

    # 2. Attempt execution against ACC-9999
    with pytest.raises(ActionNotAllowedError) as exc_info:
        action_service.execute(
            action="freeze_account",
            account_id="ACC-9999",
            approval_id=approval_id,
            executed_by="attacker@evil.corp",
        )
    assert "Approval does not authorize this account" in str(exc_info.value)

    # 3. Verify target account ACC-9999 was NOT modified and denial audited
    with SessionFactory() as session:
        acc9999 = session.scalar(
            select(Account).where(Account.account_id == "ACC-9999")
        )
        assert acc9999 is not None
        assert acc9999.status == "active"

        denials = find_by_event_type(session, AuditEventType.ACTION_EXECUTION_DENIED)
        assert len(denials) >= 1
        assert denials[-1].details.get("reason_code") == "argument_mismatch"



def test_direct_freeze_account_rejects_argument_mismatch():
    """freeze_account directly checks that account_id matches approved arguments."""
    approval = request_action_approval(
        ProposedAction(
            action="freeze_account",
            account_id="ACC-1001",
            reason="Risk alert.",
        )
    )
    approved = approve_action(
        approval_id=approval.approval_id,
        decided_by="compliance@example.com",
    )

    with pytest.raises(ActionNotAllowedError) as exc_info:
        freeze_account(
            account_id="ACC-9999",
            approval_id=approved.approval_id,
            actor="attacker@evil.corp",
        )

    assert "Approval does not authorize this account" in str(exc_info.value)

    with SessionFactory() as session:
        denials = find_by_event_type(session, AuditEventType.ACTION_EXECUTION_DENIED)
        assert len(denials) >= 1
        assert denials[-1].details.get("reason_code") == "argument_mismatch"
        assert denials[-1].details.get("action") == "freeze_account"


def test_unsupported_action_rejected(action_service: ActionService):
    """ActionService must reject unsupported or mutated action names."""
    with pytest.raises(ActionNotAllowedError) as exc_info:
        action_service.execute(
            action="unfreeze_account",
            account_id="ACC-1001",
            approval_id="some-id",
        )
    assert "Unsupported action" in str(exc_info.value)
