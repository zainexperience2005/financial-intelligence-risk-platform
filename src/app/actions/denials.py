import logging
from enum import StrEnum
from typing import Any

from app.core.exceptions import ActionNotAllowedError
from app.services.audit import AuditService
from kit.security.redaction import redact_mapping

logger = logging.getLogger(__name__)


class ActionDenialCode(StrEnum):
    APPROVAL_NOT_FOUND = "approval_not_found"
    APPROVAL_PENDING = "approval_pending"
    APPROVAL_REJECTED = "approval_rejected"
    APPROVAL_ALREADY_EXECUTED = "approval_already_executed"
    ACTION_MISMATCH = "action_mismatch"
    ARGUMENT_MISMATCH = "argument_mismatch"
    ACCOUNT_NOT_FOUND = "account_not_found"


def deny_action(
    *,
    audit_service: AuditService | None = None,
    actor: str,
    action: str,
    approval_id: str | None,
    code: ActionDenialCode,
    reason: str,
    arguments: dict[str, Any],
) -> None:
    """Audits a denied action in a separate committed transaction.

    Raises ActionNotAllowedError.

    Fail-closed invariant: If audit writing fails, the error is logged, but
    ActionNotAllowedError is still raised unconditionally.
    """
    svc = audit_service or AuditService()
    safe_arguments = redact_mapping(arguments)

    details = {
        "action": action,
        "approval_id": approval_id,
        "reason_code": code.value,
        "reason": reason,
        "arguments": safe_arguments,
    }

    try:
        svc.record_denied_action(
            actor=actor,
            action=action,
            entity_id=approval_id,
            details=details,
        )
    except Exception as exc:
        logger.warning("Failed to persist denied-action audit: %s", exc)

    raise ActionNotAllowedError(reason)
