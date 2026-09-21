from kit.rag import RetrievedChunk
from kit.vectorstores.qdrant import (
    create_qdrant_store,
)


def retrieve_chunks(
    query: str,
    k: int = 4,
) -> list[RetrievedChunk]:
    store = create_qdrant_store()

    results = store.similarity_search_with_score(
        query=query,
        k=k,
    )

    chunks: list[RetrievedChunk] = []

    for document, score in results:
        chunks.append(
            RetrievedChunk(
                content=document.page_content,
                source=str(
                    document.metadata.get(
                        "source",
                        "unknown",
                    )
                ),
                chunk_id=document.metadata.get("chunk_id"),
                score=float(score),
            )
        )

    return chunks
