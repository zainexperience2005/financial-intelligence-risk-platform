from pydantic import BaseModel, Field


class PolicyCitation(BaseModel):
    source: str
    chunk_id: str | None = None


class PolicyAnalysisResult(BaseModel):
    summary: str

    grounded: bool = False

    citations: list[PolicyCitation] = Field(default_factory=list)

    retrieved_chunk_count: int = Field(
        default=0,
        ge=0,
    )
    retrieval_relevance: str | None = None

    correction_used: bool = False

    retrieval_attempts: int = Field(
        default=0,
        ge=0,
    )
