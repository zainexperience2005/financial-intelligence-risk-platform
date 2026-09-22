from pydantic import BaseModel, Field


class InvestigationMemoryContext(BaseModel):
    memory_id: str
    content: str
    transaction_id: str | None = None
    created_at: str | None = None
    ruleset_version: str | None = None
    relevance_score: float | None = None


class MemoryContext(BaseModel):
    memories: list[InvestigationMemoryContext] = Field(default_factory=list)
    truncated: bool = False
