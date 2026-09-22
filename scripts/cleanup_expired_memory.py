"""Maintenance script for deleting expired long-term memory records.

Run manually or via scheduled cron/maintenance jobs.
"""

import logging
from datetime import UTC, datetime

from kit.config import get_settings
from kit.memory.store import delete_memory, is_memory_expired
from kit.vectorstores.qdrant import create_qdrant_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup_expired_memory")


def cleanup_expired_memories() -> int:
    """Scans memory collection and deletes records whose retention TTL has expired."""
    settings = get_settings()

    try:
        store = create_qdrant_store(settings.memory_qdrant_collection)
    except Exception as exc:
        logger.warning(f"Could not connect to Qdrant memory store: {exc}")
        return 0

    now = datetime.now(UTC)
    deleted_count = 0

    try:
        # Search or scroll to find expired memories
        # Using similarity search with empty or wildcard query to inspect items
        results = store.similarity_search_with_score("", k=100)
        for doc, _ in results:
            memory_id = doc.metadata.get("memory_id")
            expires_at_raw = doc.metadata.get("expires_at")
            if not memory_id or not expires_at_raw:
                continue

            try:
                expires_at = datetime.fromisoformat(expires_at_raw)
            except (ValueError, TypeError):
                continue

            if is_memory_expired(expires_at, now):
                delete_memory(memory_id)
                deleted_count += 1
                logger.info(f"Deleted expired memory record: {memory_id}")
    except Exception as exc:
        logger.warning(f"Error during memory cleanup: {exc}")

    logger.info(f"Cleanup finished. Total expired memories deleted: {deleted_count}")
    return deleted_count


if __name__ == "__main__":
    cleanup_expired_memories()
