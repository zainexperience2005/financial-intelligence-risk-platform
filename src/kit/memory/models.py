from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

MemoryType = Literal[
    "fact",
    "preference",
    "summary",
    "investigation",
]


class MemoryRecord(BaseModel):
    memory_id: str = Field(default_factory=lambda: str(uuid4()))

    content: str = Field(min_length=1)

    memory_type: MemoryType

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    expires_at: datetime | None = None

    metadata: dict[str, str] = Field(default_factory=dict)


class MemorySearchResult(BaseModel):
    memory_id: str
    content: str
    memory_type: MemoryType
    score: float | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
