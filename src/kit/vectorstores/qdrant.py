from langchain_qdrant import QdrantVectorStore

from kit.config import get_settings
from kit.embeddings import create_embeddings


def create_qdrant_store(
    collection_name: str | None = None,
) -> QdrantVectorStore:
    settings = get_settings()

    target_collection = collection_name or settings.qdrant_collection

    return QdrantVectorStore.from_existing_collection(
        embedding=create_embeddings(),
        collection_name=target_collection,
        url=settings.qdrant_url,
    )
