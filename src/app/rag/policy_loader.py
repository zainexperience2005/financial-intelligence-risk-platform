from pathlib import Path

from kit.rag.documents import SourceDocument


def load_policy_documents(
    directory: Path,
) -> list[SourceDocument]:
    documents: list[SourceDocument] = []

    for path in sorted(directory.glob("*.md")):
        content = path.read_text(encoding="utf-8")

        documents.append(
            SourceDocument(
                content=content,
                source=path.name,
                metadata={
                    "document_type": "financial_policy",
                },
            )
        )

    return documents
