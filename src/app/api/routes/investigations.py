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
    request: InvestigationRequest,
    service: InvestigationService = Depends(get_investigation_service),
) -> InvestigationResponse:
    return await service.investigate(
        question=request.question,
        thread_id=request.thread_id,
    )
