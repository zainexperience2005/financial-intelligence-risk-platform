from app.actions.denials import ActionDenialCode, deny_action
from app.audit.events import AuditEventType
from app.db.repositories.accounts import (
    freeze_account_record,
    get_account_by_business_id,
)
from app.db.repositories.approvals import (
    get_approval_for_update,
    mark_approval_executed,
)
from app.db.repositories.audit import (
    record_audit_event,
)
from app.schemas import ActionResult
from app.services.audit import AuditService
from kit.databases.session import (
    SessionFactory,
)


def freeze_account(
    *,
    account_id: str,
    approval_id: str,
    actor: str,
    audit_service: AuditService | None = None,
) -> ActionResult:
    """Executes an authorized account freeze mutation within an atomic transaction.

    Security Architecture:
    - Denied actions: Action transaction is rolled back, and the denial is recorded
      via an independent committed audit transaction through deny_action.
    - Successful actions: Account update, approval consumption, and success audit
      are executed in one single atomic transaction.
    """
    with SessionFactory() as session:
        approval = get_approval_for_update(
            session,
            approval_id,
        )

        if approval is None:
            session.rollback()
            deny_action(
                audit_service=audit_service,
                actor=actor,
                action="freeze_account",
                approval_id=approval_id,
                code=ActionDenialCode.APPROVAL_NOT_FOUND,
                reason="Valid approval is required.",
                arguments={"account_id": account_id},
            )

        if approval.status != "approved":
            session.rollback()
            if approval.status == "executed":
                code = ActionDenialCode.APPROVAL_ALREADY_EXECUTED
            elif approval.status == "pending":
                code = ActionDenialCode.APPROVAL_PENDING
            elif approval.status == "rejected":
                code = ActionDenialCode.APPROVAL_REJECTED
            else:
                code = ActionDenialCode.APPROVAL_NOT_FOUND

            deny_action(
                audit_service=audit_service,
                actor=actor,
                action="freeze_account",
                approval_id=approval_id,
                code=code,
                reason="Action has not been approved.",
                arguments={"account_id": account_id},
            )

        if approval.action != "freeze_account":
            session.rollback()
            deny_action(
                audit_service=audit_service,
                actor=actor,
                action="freeze_account",
                approval_id=approval_id,
                code=ActionDenialCode.ACTION_MISMATCH,
                reason="Approval does not authorize this action.",
                arguments={
                    "account_id": account_id,
                    "approved_action": approval.action,
                },
            )

        approved_account = approval.arguments.get("account_id")

        if approved_account != account_id:
            session.rollback()
            deny_action(
                audit_service=audit_service,
                actor=actor,
                action="freeze_account",
                approval_id=approval_id,
                code=ActionDenialCode.ARGUMENT_MISMATCH,
                reason="Approval does not authorize this account.",
                arguments={
                    "requested_account_id": account_id,
                    "approved_account_id": approved_account,
                },
            )

        account = get_account_by_business_id(
            session,
            account_id,
        )

        if account is None:
            session.rollback()
            deny_action(
                audit_service=audit_service,
                actor=actor,
                action="freeze_account",
                approval_id=approval_id,
                code=ActionDenialCode.ACCOUNT_NOT_FOUND,
                reason="Account not found.",
                arguments={"account_id": account_id},
            )

        # Atomic transaction: account freeze + mark approval executed + audit record
        try:
            freeze_account_record(account)
            mark_approval_executed(approval)
            record_audit_event(
                session,
                event_type=AuditEventType.ACTION_EXECUTED,
                actor=actor,
                entity_type="account",
                entity_id=account_id,
                details={
                    "action": "freeze_account",
                    "approval_id": approval_id,
                    "new_status": "frozen",
                },
            )
            session.commit()

            return ActionResult(
                action="freeze_account",
                account_id=account_id,
                success=True,
                message=f"Account {account_id} was frozen.",
            )

        except Exception:
            session.rollback()
            raise
