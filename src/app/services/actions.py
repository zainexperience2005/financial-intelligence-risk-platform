from app.actions.freeze_account import freeze_account
from app.core.exceptions import ActionNotAllowedError
from app.db.models import ApprovalRecord
from app.schemas import ActionResult, ProposedAction
from app.services.approvals import request_action_approval


class ActionService:
    def propose(
        self,
        action: ProposedAction,
    ) -> ApprovalRecord:
        """Proposes a protected customer action and requests approval."""
        return request_action_approval(action)

    def execute(
        self,
        *,
        action: str,
        account_id: str,
        approval_id: str,
        executed_by: str = "analyst@example.com",
    ) -> ActionResult:
        """Executes a protected customer action against verified approval."""
        if action != "freeze_account":
            raise ActionNotAllowedError("Unsupported action.")

        result = freeze_account(
            account_id=account_id,
            approval_id=approval_id,
            actor=executed_by,
        )

        if not result.success:
            raise ActionNotAllowedError(result.message)

        return result
