from kit.rag.documents import (
    DocumentChunk,
    SourceDocument,
)


def chunk_document(
    document: SourceDocument,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[DocumentChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if overlap < 0:
        raise ValueError("overlap cannot be negative.")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    text = document.content.strip()

    if not text:
        return []

    chunks: list[DocumentChunk] = []

    start = 0
    index = 0

    while start < len(text):
        end = min(
            start + chunk_size,
            len(text),
        )

        content = text[start:end].strip()

        if content:
            chunks.append(
                DocumentChunk(
                    content=content,
                    source=document.source,
                    chunk_id=(f"{document.source}:{index}"),
                    metadata=document.metadata,
                )
            )

        if end == len(text):
            break

        start = end - overlap
        index += 1

    return chunks
