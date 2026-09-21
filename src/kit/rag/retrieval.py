from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    content: str

    source: str

    chunk_id: str | None = None

    score: float | None = None
