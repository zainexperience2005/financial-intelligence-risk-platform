from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.schemas import InvestigationResponse
from app.services import database_is_healthy
from kit.config import get_settings
from app.graphs import build_financial_graph


router = APIRouter()

financial_graph = build_financial_graph()
class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str = Field(min_length=1)


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Performs a health check of the API."""
    settings = get_settings()
    db_healthy = database_is_healthy()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.post(
    "/chat",
    response_model=InvestigationResponse,
)
async def chat(
    request: ChatRequest,
) -> InvestigationResponse:
    result = financial_graph.invoke(
        {
            "question": request.message,
        }
    )

    return InvestigationResponse(
        analysis=result["analysis"],
        plan=result["plan"],
        data_required=result.get(
            "data_required",
            False,
        ),
        message=result.get("data_message"),
    )