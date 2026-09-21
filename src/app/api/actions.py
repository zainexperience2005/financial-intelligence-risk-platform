"""Backward compatibility re-exports for actions API."""

from app.api.routes.actions import (
    ExecuteActionRequest,
    execute_action,
    propose_action,
    router,
)

__all__ = [
    "ExecuteActionRequest",
    "execute_action",
    "propose_action",
    "router",
]
