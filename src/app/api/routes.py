from uuid import uuid4

from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from app.graphs import build_financial_graph
from app.schemas import InvestigationResponse
from app.services import database_is_healthy
from kit.config import get_settings

router = APIRouter()

# Default standalone graph fallback
default_graph = build_financial_graph()


class ChatRequest(BaseModel):
    """Request model for conversational investigations."""

    message: str | None = None
    question: str | None = None
    thread_id: str | None = Field(default=None, min_length=1)

    @property
    def query(self) -> str:
        return self.question or self.message or ""


class InvestigationRequest(BaseModel):
    """Explicit investigation request model with mandatory thread_id."""

    question: str = Field(min_length=1)
    thread_id: str = Field(min_length=1)


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


def _run_investigation(
    *,
    question: str,
    thread_id: str,
    graph,
) -> InvestigationResponse:
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    result = graph.invoke(
        {
            "question": question,
            "messages": [HumanMessage(content=question)],
        },
        config=config,
    )

    return InvestigationResponse(
        plan=result["plan"],
        report=result["report"],
        sql_analysis=result.get("sql_analysis"),
        data_analysis=result.get("data_analysis"),
        policy_analysis=result.get("policy_analysis"),
        risk_analysis=result.get("risk_analysis"),
    )


@router.post(
    "/chat",
    response_model=InvestigationResponse,
)
def chat(
    request: ChatRequest,
    http_request: Request,
) -> InvestigationResponse:
    query = request.query
    if not query:
        raise ValueError("Either 'message' or 'question' must be provided.")

    thread_id = request.thread_id or str(uuid4())
    graph = getattr(http_request.app.state, "financial_graph", default_graph)

    return _run_investigation(
        question=query,
        thread_id=thread_id,
        graph=graph,
    )


@router.post(
    "/investigate",
    response_model=InvestigationResponse,
)
def investigate(
    payload: InvestigationRequest,
    http_request: Request,
) -> InvestigationResponse:
    graph = getattr(http_request.app.state, "financial_graph", default_graph)

    return _run_investigation(
        question=payload.question,
        thread_id=payload.thread_id,
        graph=graph,
    )
