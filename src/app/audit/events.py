from enum import StrEnum


class AuditEventType(StrEnum):
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"

    ACTION_EXECUTED = "action_executed"
    ACTION_EXECUTION_DENIED = "action_execution_denied"

    APPROVAL_NOT_FOUND = "approval_not_found"
    APPROVAL_NOT_APPROVED = "approval_not_approved"
    APPROVAL_REPLAY_ATTEMPT = "approval_replay_attempt"
    APPROVAL_ACTION_MISMATCH = "approval_action_mismatch"
    APPROVAL_ARGUMENT_MISMATCH = "approval_argument_mismatch"
