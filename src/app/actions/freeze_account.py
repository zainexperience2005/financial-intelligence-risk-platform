from app.db.repositories.accounts import (
    freeze_account_record,
    get_account_by_business_id,
)
from app.db.repositories.approvals import (
    get_approval,
    mark_approval_executed,
)
from app.db.repositories.audit import (
    record_audit_event,
)
from app.schemas import ActionResult
from kit.databases.session import (
    SessionFactory,
)


def freeze_account(
    *,
    account_id: str,
    approval_id: str,
    actor: str,
) -> ActionResult:
    """Executes an authorized account freeze mutation within an atomic transaction."""
    with SessionFactory() as session:
        approval = get_approval(
            session,
            approval_id,
        )

        if approval is None:
            return ActionResult(
                action="freeze_account",
                account_id=account_id,
                success=False,
                message="Valid approval is required.",
            )

        if approval.status != "approved":
            return ActionResult(
                action="freeze_account",
                account_id=account_id,
                success=False,
                message="Action has not been approved.",
            )

        if approval.action != "freeze_account":
            return ActionResult(
                action="freeze_account",
                account_id=account_id,
                success=False,
                message="Approval does not authorize this action.",
            )

        approved_account = approval.arguments.get("account_id")

        if approved_account != account_id:
            return ActionResult(
                action="freeze_account",
                account_id=account_id,
                success=False,
                message="Approval does not authorize this account.",
            )

        account = get_account_by_business_id(
            session,
            account_id,
        )

        if account is None:
            return ActionResult(
                action="freeze_account",
                account_id=account_id,
                success=False,
                message="Account not found.",
            )

        # Atomic transaction: account freeze + mark approval executed + audit record
        try:
            freeze_account_record(account)

            mark_approval_executed(approval)

            record_audit_event(
                session,
                event_type="action_executed",
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
