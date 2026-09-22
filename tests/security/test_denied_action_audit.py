"""Security tests verifying denied-action auditing and fail-closed boundaries."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import select

from app.actions.denials import ActionDenialCode, deny_action
from app.actions.freeze_account import freeze_account
from app.audit.events import AuditEventType
from app.core.exceptions import ActionNotAllowedError
from app.db.models import Account, ApprovalRecord
from app.db.repositories.audit import find_by_event_type
from app.schemas import ProposedAction
from app.services.actions import ActionService
from app.services.approvals import approve_action, request_action_approval
from app.services.audit import AuditService
from kit.databases.session import SessionFactory


def test_denial_auditing_fails_closed(action_service: ActionService):
    """If audit service crashes during denial logging, action is strictly denied."""
    faulty_audit_service = MagicMock(spec=AuditService)
    faulty_audit_service.record_denied_action.side_effect = RuntimeError(
        "Audit DB down!"
    )

    with pytest.raises(ActionNotAllowedError) as exc_info:
        freeze_account(
            account_id="ACC-1001",
            approval_id="fabricated-approval-id",
            actor="attacker@evil.corp",
            audit_service=faulty_audit_service,
        )

    assert "Valid approval is required" in str(exc_info.value)
    faulty_audit_service.record_denied_action.assert_called_once()

    # Verify target account was not touched
    with SessionFactory() as session:
        acc = session.scalar(select(Account).where(Account.account_id == "ACC-1001"))
        assert acc is not None
        assert acc.status == "active"


def test_success_audit_failure_rolls_back_entire_transaction():
    """If success audit recording fails, mutation and approval roll back."""
    # 1. Propose & approve
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

    # 2. Mock record_audit_event to fail during atomic execution
    with patch(
        "app.actions.freeze_account.record_audit_event",
        side_effect=RuntimeError("Audit write failed!"),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            freeze_account(
                account_id="ACC-1001",
                approval_id=approval_id,
                actor="analyst@example.com",
            )
        assert "Audit write failed!" in str(exc_info.value)

    # 3. Verify that account was NOT frozen and approval was NOT consumed
    with SessionFactory() as session:
        acc = session.scalar(select(Account).where(Account.account_id == "ACC-1001"))
        assert acc is not None
        assert acc.status == "active"

        app_rec = session.scalar(
            select(ApprovalRecord).where(ApprovalRecord.approval_id == approval_id)
        )
        assert app_rec is not None
        assert app_rec.status == "approved"  # Still approved, not executed


def test_denial_audit_redacts_sensitive_arguments():
    """Denial audit logs must redact sensitive arguments before saving to DB."""
    with pytest.raises(ActionNotAllowedError):
        deny_action(
            actor="probe_user",
            action="freeze_account",
            approval_id="test-approval-id",
            code=ActionDenialCode.APPROVAL_NOT_FOUND,
            reason="Test sensitive redaction",
            arguments={
                "account_id": "ACC-1001",
                "api_key": "sk-live-secret-123456",
                "password": "super-secret-password",
            },
        )

    with SessionFactory() as session:
        denials = find_by_event_type(session, AuditEventType.ACTION_EXECUTION_DENIED)
        assert len(denials) >= 1
        redacted_event = next(
            ev
            for ev in reversed(denials)
            if ev.details.get("reason") == "Test sensitive redaction"
        )
        assert redacted_event.details["arguments"]["api_key"] == "[REDACTED]"
        assert redacted_event.details["arguments"]["password"] == "[REDACTED]"
        assert redacted_event.details["arguments"]["account_id"] == "ACC-1001"

