from kit.crag.models import (
    RetrievalEvaluation,
)
from kit.crag.pipeline import (
    corrective_retrieve,
)
from kit.rag import RetrievedChunk


def test_relevant_retrieval_skips_correction():
    chunks = [
        RetrievedChunk(
            content="Approval is required.",
            source="policy.md",
            chunk_id="policy.md:0",
        )
    ]

    def retriever(query, k):
        return chunks

    def evaluator(query, evidence):
        return RetrievalEvaluation(
            relevance="relevant",
            reason="Direct evidence.",
            useful_chunk_ids=["policy.md:0"],
        )

    def rewriter(query, reason):
        raise AssertionError("Rewriter should not be called.")

    result = corrective_retrieve(
        query="Is approval required?",
        retriever=retriever,
        evaluator=evaluator,
        rewriter=rewriter,
    )

    assert result.correction_used is False
    assert result.retrieval_attempts == 1
    assert result.answerable is True
    assert len(result.chunks) == 1
    assert result.chunks[0].chunk_id == "policy.md:0"


def test_irrelevant_retrieval_triggers_correction_and_recovers():
    initial_chunks = [
        RetrievedChunk(
            content="Unrelated bank opening hours.",
            source="general.md",
            chunk_id="general.md:0",
        )
    ]

    corrected_chunks = [
        RetrievedChunk(
            content="Account restrictions require approval.",
            source="restrictions.md",
            chunk_id="restrictions.md:0",
        )
    ]

    queries_retrieved = []

    def retriever(query, k):
        queries_retrieved.append(query)
        if len(queries_retrieved) == 1:
            return initial_chunks
        return corrected_chunks

    eval_calls = []

    def evaluator(query, evidence):
        eval_calls.append(evidence)
        if len(eval_calls) == 1:
            return RetrievalEvaluation(
                relevance="irrelevant",
                reason="Only contains bank hours.",
                useful_chunk_ids=[],
            )
        return RetrievalEvaluation(
            relevance="relevant",
            reason="Direct restriction policy found.",
            useful_chunk_ids=["restrictions.md:0"],
        )

    def rewriter(query, reason):
        return "account restrictions human approval policy"

    result = corrective_retrieve(
        query="Can an AI freeze an account?",
        retriever=retriever,
        evaluator=evaluator,
        rewriter=rewriter,
    )

    assert result.correction_used is True
    assert result.retrieval_attempts == 2
    assert result.answerable is True
    assert result.final_query == "account restrictions human approval policy"
    assert len(result.chunks) == 1
    assert result.chunks[0].source == "restrictions.md"


def test_irrelevant_retrieval_stays_irrelevant_and_unanswerable():
    weak_chunks = [
        RetrievedChunk(
            content="General transaction limits.",
            source="limits.md",
            chunk_id="limits.md:0",
        )
    ]

    def retriever(query, k):
        return weak_chunks

    def evaluator(query, evidence):
        return RetrievalEvaluation(
            relevance="irrelevant",
            reason="No cryptocurrency policies exist.",
            useful_chunk_ids=[],
        )

    def rewriter(query, reason):
        return "cryptocurrency wallet policy"

    result = corrective_retrieve(
        query="What is crypto policy?",
        retriever=retriever,
        evaluator=evaluator,
        rewriter=rewriter,
    )

    assert result.correction_used is True
    assert result.retrieval_attempts == 2
    assert result.answerable is False
    assert len(result.chunks) == 0
