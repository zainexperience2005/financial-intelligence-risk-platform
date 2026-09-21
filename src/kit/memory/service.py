from datetime import UTC, datetime, timedelta

from kit.memory.models import (
    MemoryRecord,
    MemorySearchResult,
    MemoryType,
)
from kit.memory.store import (
    delete_memory,
    search_memories,
    store_memory,
)


class MemoryService:
    """Service providing durable long-term memory operations."""

    def remember(
        self,
        *,
        content: str,
        memory_type: MemoryType,
        retention_days: int | None = None,
        metadata: dict[str, str] | None = None,
    ) -> MemoryRecord:
        """Stores a new memory record with optional retention window."""
        expires_at = None

        if retention_days is not None:
            expires_at = datetime.now(UTC) + timedelta(days=retention_days)

        memory = MemoryRecord(
            content=content,
            memory_type=memory_type,
            expires_at=expires_at,
            metadata=metadata or {},
        )

        return store_memory(memory)

    def recall(
        self,
        query: str,
        *,
        k: int = 5,
    ) -> list[MemorySearchResult]:
        """Searches long-term memories relevant to the given query."""
        return search_memories(
            query,
            k=k,
        )

    def forget(
        self,
        memory_id: str,
    ) -> None:
        """Deletes a long-term memory by its ID."""
        delete_memory(memory_id)
