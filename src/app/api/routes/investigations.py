"""Investigations route — POST /api/v1/investigations.

Accepts a natural-language question and a thread_id, delegates to
InvestigationService which invokes the LangGraph multi-agent graph,
and returns a structured InvestigationResponse.

This router is a pure transport boundary: no agent orchestration,
business rules, or database mutations live here.
"""

from fastapi import (
    APIRouter,
    Depends,
    Request,
)

from app.api.dependencies import (
    get_investigation_service,
)
from app.api.schemas.investigations import (
    InvestigationRequest,
    InvestigationResponse,
)
from app.services.investigation import (
    InvestigationService,
)

router = APIRouter(
    prefix="/investigations",
    tags=["investigations"],
)


@router.post(
    "",
    response_model=InvestigationResponse,
)
async def investigate(
    payload: InvestigationRequest,
    http_request: Request,
    service: InvestigationService = Depends(get_investigation_service),
) -> InvestigationResponse:
    request_id = getattr(http_request.state, "request_id", None)
    return await service.investigate(
        question=payload.question,
        thread_id=payload.thread_id,
        request_id=request_id,
    )
