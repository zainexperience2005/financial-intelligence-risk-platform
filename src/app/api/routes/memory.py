from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.memory import AppMemoryService
from kit.memory import MemoryRecord, MemorySearchResult

router = APIRouter(
    prefix="/memory",
    tags=["memory"],
)

memory_service = AppMemoryService()



class RememberRequest(BaseModel):
    content: str = Field(min_length=1)
    retention_days: int = Field(
        default=30,
        ge=1,
        le=365,
    )


class RecallRequest(BaseModel):
    query: str = Field(min_length=1)
    k: int = Field(
        default=5,
        ge=1,
        le=10,
    )


@router.post("", response_model=MemoryRecord)
def remember(
    request: RememberRequest,
) -> MemoryRecord:
    """Explicitly stores content in long-term memory."""
    return memory_service.remember(
        content=request.content,
        memory_type="investigation",
        retention_days=request.retention_days,
        metadata={
            "source": "explicit_api",
        },
    )


@router.post("/recall", response_model=list[MemorySearchResult])
def recall(
    request: RecallRequest,
) -> list[MemorySearchResult]:
    """Retrieves long-term memories relevant to the search query."""
    return memory_service.recall(
        request.query,
        k=request.k,
    )


@router.delete("/{memory_id}")
def forget(
    memory_id: str,
) -> dict[str, str | bool]:
    """Deletes a long-term memory by ID."""
    memory_service.forget(memory_id)

    return {
        "deleted": True,
        "memory_id": memory_id,
    }
