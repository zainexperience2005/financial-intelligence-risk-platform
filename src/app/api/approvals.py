"""Backward compatibility re-exports for approvals API."""

from app.api.routes.approvals import (
    ApprovalDecisionRequest,
    approve,
    get_approval,
    reject,
    router,
)
from app.api.routes.approvals import (
    ApprovalDecisionRequest as DecisionRequest,
)

__all__ = [
    "ApprovalDecisionRequest",
    "DecisionRequest",
    "approve",
    "get_approval",
    "reject",
    "router",
]
