from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agents.financial_assistant import ask_financial_assistant
from kit.config import get_settings

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    answer: str


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Performs a health check of the API."""
    settings = get_settings()

    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Sends a chat message to the financial assistant and returns the response.
    """
    answer = ask_financial_assistant(request.message)

    return ChatResponse(answer=answer)