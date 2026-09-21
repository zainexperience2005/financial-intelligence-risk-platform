from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.actions.freeze_account import freeze_account
from app.schemas import ActionResult, ProposedAction
from app.services.approvals import (
    request_action_approval,
)

router = APIRouter(
    prefix="/actions",
    tags=["actions"],
)


@router.post("/propose")
def propose_action(
    action: ProposedAction,
):
    return request_action_approval(action)


class ExecuteActionRequest(BaseModel):
    action: str
    account_id: str
    approval_id: str
    executed_by: str = "analyst@example.com"


@router.post("/execute", response_model=ActionResult)
def execute_action(
    request: ExecuteActionRequest,
):
    if request.action != "freeze_account":
        raise HTTPException(
            status_code=400,
            detail="Unsupported action.",
        )

    result = freeze_account(
        account_id=request.account_id,
        approval_id=request.approval_id,
        actor=request.executed_by,
    )

    if not result.success:
        raise HTTPException(
            status_code=403,
            detail=result.message,
        )

    return result
