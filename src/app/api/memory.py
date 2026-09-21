"""Backward compatibility re-exports for memory API."""

from app.api.routes.memory import (
    RecallRequest,
    RememberRequest,
    forget,
    memory_service,
    recall,
    remember,
    router,
)

__all__ = [
    "RecallRequest",
    "RememberRequest",
    "forget",
    "memory_service",
    "recall",
    "remember",
    "router",
]
