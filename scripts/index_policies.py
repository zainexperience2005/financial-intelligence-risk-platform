from pathlib import Path

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore

from app.rag.policy_loader import (
    load_policy_documents,
)
from kit.config import get_settings
from kit.embeddings import create_embeddings
from kit.rag import chunk_document


def main() -> None:
    settings = get_settings()

    policy_directory = Path("data/policies")

    documents = load_policy_documents(policy_directory)

    chunks = []

    for document in documents:
        chunks.extend(chunk_document(document))

    langchain_documents = [
        Document(
            page_content=chunk.content,
            metadata={
                **chunk.metadata,
                "source": chunk.source,
                "chunk_id": chunk.chunk_id,
            },
        )
        for chunk in chunks
    ]

    QdrantVectorStore.from_documents(
        documents=langchain_documents,
        embedding=create_embeddings(),
        url=settings.qdrant_url,
        collection_name=settings.qdrant_collection,
        force_recreate=True,
    )

    print(f"Indexed {len(chunks)} policy chunks from {len(documents)} documents.")


if __name__ == "__main__":
    main()
