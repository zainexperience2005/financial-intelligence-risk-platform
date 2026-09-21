from typing import Literal

from pydantic import BaseModel, Field

from kit.rag import RetrievedChunk


class RetrievalEvaluation(BaseModel):
    relevance: Literal[
        "relevant",
        "partial",
        "irrelevant",
    ]

    reason: str

    useful_chunk_ids: list[str] = Field(default_factory=list)


class CRAGResult(BaseModel):
    chunks: list[RetrievedChunk] = Field(default_factory=list)

    initial_evaluation: RetrievalEvaluation

    final_evaluation: RetrievalEvaluation

    original_query: str

    final_query: str

    correction_used: bool = False

    retrieval_attempts: int = Field(ge=1)

    @property
    def answerable(self) -> bool:
        return self.final_evaluation.relevance in {"relevant", "partial"} and bool(
            self.chunks
        )
