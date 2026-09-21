from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from kit.config import get_settings
from kit.embeddings import create_embeddings


def create_qdrant_store() -> QdrantVectorStore:
    settings = get_settings()

    _client = QdrantClient(url=settings.qdrant_url)

    embeddings = create_embeddings()

    return QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=settings.qdrant_collection,
        url=settings.qdrant_url,
    )
