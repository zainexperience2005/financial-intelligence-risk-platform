from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ApprovalRequest(BaseModel):
    approval_id: str = Field(default_factory=lambda: str(uuid4()))

    action: str
    arguments: dict[str, Any]

    reason: str

    status: Literal["pending", "approved", "rejected", "executed"] = "pending"

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ApprovalDecision(BaseModel):
    approval_id: str

    decision: Literal[
        "approved",
        "rejected",
    ]

    decided_by: str
    reason: str | None = None

    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
