from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.approvals import (
    approve_action,
    get_action_approval,
    reject_action,
)

router = APIRouter(
    prefix="/approvals",
    tags=["approvals"],
)


class DecisionRequest(BaseModel):
    decided_by: str
    reason: str | None = None


@router.get("/{approval_id}")
def get_approval(
    approval_id: str,
):
    approval = get_action_approval(approval_id)

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval not found.",
        )

    return approval


@router.post("/{approval_id}/approve")
def approve(
    approval_id: str,
    request: DecisionRequest,
):
    try:
        return approve_action(
            approval_id=approval_id,
            decided_by=request.decided_by,
            reason=request.reason,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post("/{approval_id}/reject")
def reject(
    approval_id: str,
    request: DecisionRequest,
):
    try:
        return reject_action(
            approval_id=approval_id,
            decided_by=request.decided_by,
            reason=request.reason,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
