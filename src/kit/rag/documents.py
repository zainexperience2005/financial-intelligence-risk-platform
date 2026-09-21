from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    content: str

    source: str

    metadata: dict[str, str] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    content: str

    source: str

    chunk_id: str

    metadata: dict[str, str] = Field(default_factory=dict)
