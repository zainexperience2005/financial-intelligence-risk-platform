"""Approvals route — GET/POST /api/v1/approvals/{approval_id}.

Provides human review endpoints for the approval workflow:
  GET  /approvals/{id}          — inspect a pending or decided approval
  POST /approvals/{id}/approve  — approve a proposed action
  POST /approvals/{id}/reject   — reject a proposed action

ApprovalDecisionRequest accepts either 'actor' or 'decided_by' to
support both field-name conventions from API clients.
"""

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
)
from pydantic import BaseModel, model_validator

from app.api.dependencies import (
    get_approval_service,
)
from app.services.approvals import (
    ApprovalService,
)

router = APIRouter(
    prefix="/approvals",
    tags=["approvals"],
)


class ApprovalDecisionRequest(BaseModel):
    actor: str = "analyst@example.com"
    decided_by: str | None = None
    reason: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_actor(cls, data: Any) -> Any:
        if isinstance(data, dict):
            actor = data.get("actor") or data.get("decided_by")
            if actor:
                data["actor"] = actor
                data["decided_by"] = actor
        return data


@router.get("/{approval_id}")
def get_approval(
    approval_id: str,
    service: ApprovalService = Depends(get_approval_service),
):
    return service.get(approval_id)


@router.post("/{approval_id}/approve")
def approve(
    approval_id: str,
    request: ApprovalDecisionRequest,
    service: ApprovalService = Depends(get_approval_service),
):
    return service.approve(
        approval_id=approval_id,
        actor=request.actor,
        reason=request.reason,
    )


@router.post("/{approval_id}/reject")
def reject(
    approval_id: str,
    request: ApprovalDecisionRequest,
    service: ApprovalService = Depends(get_approval_service),
):
    return service.reject(
        approval_id=approval_id,
        actor=request.actor,
        reason=request.reason,
    )
