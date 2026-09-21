"""Chunking and retrieval preserve source evidence and enforce chunk bounds."""

from unittest.mock import Mock

import pytest
from langchain_core.documents import Document

from kit.rag import SourceDocument, chunk_document
from kit.rag.retriever import retrieve_chunks


@pytest.mark.parametrize("size,overlap", [(0, 0), (-1, 0), (4, -1), (4, 4), (4, 5)])
def test_invalid_chunk_options(size, overlap):
    with pytest.raises(ValueError):
        chunk_document(SourceDocument(content="abc", source="a"), size, overlap)


def test_chunk_overlap_and_metadata():
    source = SourceDocument(
        content="abcdefghij", source="a.md", metadata={"kind": "test"}
    )
    chunks = chunk_document(source, chunk_size=4, overlap=1)
    assert [c.content for c in chunks] == ["abcd", "defg", "ghij"]
    assert [c.chunk_id for c in chunks] == ["a.md:0", "a.md:1", "a.md:2"]
    assert all(
        c.source == source.source and c.metadata == source.metadata for c in chunks
    )


@pytest.mark.parametrize("content", ["", "  \n "])
def test_empty_document(content):
    assert chunk_document(SourceDocument(content=content, source="a")) == []


def test_document_metadata_is_not_shared():
    first = SourceDocument(content="a", source="a")
    second = SourceDocument(content="b", source="b")
    first.metadata["key"] = "value"
    assert second.metadata == {}


def test_retrieval_maps_metadata(monkeypatch):
    store = Mock()
    store.similarity_search_with_score.return_value = [
        (
            Document(
                page_content="evidence", metadata={"source": "a.md", "chunk_id": "a:0"}
            ),
            0.8,
        ),
        (Document(page_content="no metadata"), 0.2),
    ]
    monkeypatch.setattr("kit.rag.retriever.create_qdrant_store", lambda: store)
    chunks = retrieve_chunks("question", k=2)
    store.similarity_search_with_score.assert_called_once_with(query="question", k=2)
    assert chunks[0].model_dump() == {
        "content": "evidence",
        "source": "a.md",
        "chunk_id": "a:0",
        "score": 0.8,
    }
    assert chunks[1].source == "unknown"
    assert chunks[1].chunk_id is None
