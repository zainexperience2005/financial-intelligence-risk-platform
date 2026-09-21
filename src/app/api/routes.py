from fastapi import APIRouter
from pydantic import BaseModel

from app.graphs import build_financial_graph
from app.schemas import InvestigationResponse
from app.services import database_is_healthy
from kit.config import get_settings

router = APIRouter()

financial_graph = build_financial_graph()


class ChatRequest(BaseModel):
    """Request model for chat messages."""

    message: str | None = None
    question: str | None = None

    @property
    def query(self) -> str:
        return self.message or self.question or ""


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
def chat(
    request: ChatRequest,
) -> InvestigationResponse:
    query = request.query
    if not query:
        raise ValueError("Either 'message' or 'question' must be provided.")

    result = financial_graph.invoke(
        {
            "question": query,
        }
    )

    return InvestigationResponse(
        plan=result["plan"],
        report=result["report"],
        sql_analysis=result.get("sql_analysis"),
        data_analysis=result.get("data_analysis"),
        policy_analysis=result.get("policy_analysis"),
        risk_analysis=result.get("risk_analysis"),
    )
