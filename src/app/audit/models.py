from typing import Any

from pydantic import BaseModel, Field


class DeniedActionAudit(BaseModel):
    event_type: str
    actor: str
    action: str
    reason_code: str
    reason: str
    approval_id: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
