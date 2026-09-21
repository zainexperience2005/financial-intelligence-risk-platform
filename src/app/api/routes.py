from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.schemas import FinancialAnalysis
from app.agents.financial_assistant import ask_financial_assistant
from kit.config import get_settings

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str = Field(min_length=1)


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Performs a health check of the API."""
    settings = get_settings()

    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }

@router.post(
    "/chat",
    response_model=FinancialAnalysis,
)
async def chat(
    request: ChatRequest,
) -> FinancialAnalysis:
    return ask_financial_assistant(request.message)