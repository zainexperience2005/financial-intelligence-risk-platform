from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
)

from kit.config import get_settings
from kit.embeddings import create_embeddings


def main() -> None:
    settings = get_settings()

    client = QdrantClient(url=settings.qdrant_url)

    embeddings = create_embeddings()

    vector_size = len(embeddings.embed_query("memory dimension check"))

    collections = {item.name for item in client.get_collections().collections}

    if settings.memory_qdrant_collection not in collections:
        client.create_collection(
            collection_name=settings.memory_qdrant_collection,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

    print("Memory collection ready.")


if __name__ == "__main__":
    main()
