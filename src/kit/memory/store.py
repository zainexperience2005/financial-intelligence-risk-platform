from datetime import UTC, datetime

from langchain_core.documents import Document

from kit.config import get_settings
from kit.memory.models import MemoryRecord, MemorySearchResult
from kit.vectorstores.qdrant import create_qdrant_store


def is_memory_expired(
    expires_at: datetime | None,
    now: datetime,
) -> bool:
    """Checks whether a memory record's expiration timestamp has passed."""
    if expires_at is None:
        return False
    return expires_at <= now


def store_memory(
    memory: MemoryRecord,
) -> MemoryRecord:
    """Stores a memory record in the dedicated Qdrant memory collection."""
    settings = get_settings()

    store = create_qdrant_store(settings.memory_qdrant_collection)

    metadata = {
        **memory.metadata,
        "memory_id": memory.memory_id,
        "memory_type": memory.memory_type,
        "created_at": memory.created_at.isoformat(),
        "expires_at": (memory.expires_at.isoformat() if memory.expires_at else ""),
    }

    document = Document(
        page_content=memory.content,
        metadata=metadata,
    )

    store.add_documents(
        documents=[document],
        ids=[memory.memory_id],
    )

    return memory


def search_memories(
    query: str,
    *,
    k: int = 5,
) -> list[MemorySearchResult]:
    """Searches memory records in Qdrant, filtering out expired items."""
    settings = get_settings()

    store = create_qdrant_store(settings.memory_qdrant_collection)

    results = store.similarity_search_with_score(
        query,
        k=k,
    )

    now = datetime.now(UTC)

    memories: list[MemorySearchResult] = []

    for document, score in results:
        expires_at_raw = document.metadata.get("expires_at")
        expires_at: datetime | None = None

        if expires_at_raw:
            try:
                expires_at = datetime.fromisoformat(expires_at_raw)
            except (ValueError, TypeError):
                expires_at = None

        if is_memory_expired(expires_at, now):
            continue

        memories.append(
            MemorySearchResult(
                memory_id=str(document.metadata.get("memory_id", "")),
                content=document.page_content,
                memory_type=document.metadata.get("memory_type", "fact"),
                score=float(score) if score is not None else None,
                metadata={
                    key: str(value)
                    for key, value in document.metadata.items()
                    if key not in {"memory_id", "memory_type"}
                },
            )
        )

    return memories


def delete_memory(
    memory_id: str,
) -> None:
    """Deletes a memory record by its stable ID."""
    settings = get_settings()

    store = create_qdrant_store(settings.memory_qdrant_collection)

    store.delete(ids=[memory_id])
