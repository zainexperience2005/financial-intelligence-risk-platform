"""Actions route — POST /api/v1/actions.

Two endpoints implement the trust-boundary for customer-impacting mutations:

  POST /actions/propose  — creates a pending approval request and records
                           an audit event. The LLM may recommend an action;
                           this endpoint records the recommendation.

  POST /actions/execute  — executes the approved action within an atomic
                           PostgreSQL transaction. Enforces approval validity,
                           action/argument binding, and single-use consumption
                           before any mutation occurs.
"""

from fastapi import (
    APIRouter,
    Depends,
)
from pydantic import BaseModel

from app.api.dependencies import (
    get_action_service,
)
from app.schemas import ActionResult, ProposedAction
from app.services.actions import (
    ActionService,
)

router = APIRouter(
    prefix="/actions",
    tags=["actions"],
)


class ExecuteActionRequest(BaseModel):
    action: str
    account_id: str
    approval_id: str
    executed_by: str = "analyst@example.com"


@router.post("/propose")
def propose_action(
    action: ProposedAction,
    service: ActionService = Depends(get_action_service),
):
    return service.propose(action)


@router.post("/execute", response_model=ActionResult)
def execute_action(
    request: ExecuteActionRequest,
    service: ActionService = Depends(get_action_service),
) -> ActionResult:
    return service.execute(
        action=request.action,
        account_id=request.account_id,
        approval_id=request.approval_id,
        executed_by=request.executed_by,
    )
