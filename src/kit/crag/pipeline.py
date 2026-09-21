"""Corrective RAG (CRAG) pipeline for robust document retrieval.

Why CRAG?
In baseline RAG, retrieval might technically return documents, but they may be
irrelevant or insufficient. CRAG introduces an active evaluation layer:
1. Retrieve candidate chunks.
2. Evaluate evidence relevance with an LLM grader.
3. If relevant, proceed immediately with the filtered evidence.
4. If weak or irrelevant, rewrite the query to improve retrieval intent,
   retrieve again, and re-evaluate. If evidence is still missing, explicitly mark
   as unanswerable.
"""

from collections.abc import Callable

from kit.crag.evaluator import (
    evaluate_retrieval,
)
from kit.crag.models import (
    CRAGResult,
    RetrievalEvaluation,
)
from kit.crag.query_rewriter import (
    rewrite_query,
)
from kit.rag import RetrievedChunk
from kit.rag.retriever import (
    retrieve_chunks,
)

# Type aliases for dependency injection (enables unit testing without live network/DB)
Retriever = Callable[
    [str, int],
    list[RetrievedChunk],
]

Evaluator = Callable[
    [str, list[RetrievedChunk]],
    RetrievalEvaluation,
]

Rewriter = Callable[
    [str, str],
    str,
]


def corrective_retrieve(
    query: str,
    k: int = 4,
    retriever: Retriever = retrieve_chunks,
    evaluator: Evaluator = evaluate_retrieval,
    rewriter: Rewriter = rewrite_query,
) -> CRAGResult:
    """Executes bounded corrective retrieval for a user query.

    Args:
        query: The original search query.
        k: Maximum number of chunks to retrieve per search attempt.
        retriever: Retrieval function (default: Qdrant similarity search).
        evaluator: Relevance evaluator (default: LLM structured grader).
        rewriter: Query rewriter (default: intent-preserving LLM rewriter).

    Returns:
        CRAGResult containing filtered useful chunks and audit metadata.
    """
    # Step 1: Initial retrieval
    initial_chunks = retriever(
        query,
        k,
    )

    # Step 2: Evaluate whether initial evidence actually answers the query
    initial_evaluation = evaluator(
        query,
        initial_chunks,
    )

    # Step 3: Fast path - if initial evidence is sufficient, avoid extra LLM calls
    if initial_evaluation.relevance == "relevant":
        return CRAGResult(
            chunks=_filter_useful_chunks(
                initial_chunks,
                initial_evaluation.useful_chunk_ids,
            ),
            initial_evaluation=initial_evaluation,
            final_evaluation=initial_evaluation,
            original_query=query,
            final_query=query,
            correction_used=False,
            retrieval_attempts=1,
        )

    # Step 4: Corrective path - rewrite query based on why retrieval was weak
    rewritten_query = rewriter(
        query,
        initial_evaluation.reason,
    )

    # Step 5: Second retrieval attempt (bounded to 1 retry to avoid infinite loops)
    corrected_chunks = retriever(
        rewritten_query,
        k,
    )

    # Step 6: Re-evaluate the corrected evidence
    final_evaluation = evaluator(
        query,
        corrected_chunks,
    )

    final_chunks = []

    # Step 7: Only keep useful chunks if final evaluation found useful evidence
    if final_evaluation.relevance in {
        "relevant",
        "partial",
    }:
        final_chunks = _filter_useful_chunks(
            corrected_chunks,
            final_evaluation.useful_chunk_ids,
        )

    return CRAGResult(
        chunks=final_chunks,
        initial_evaluation=initial_evaluation,
        final_evaluation=final_evaluation,
        original_query=query,
        final_query=rewritten_query,
        correction_used=True,
        retrieval_attempts=2,
    )


def _filter_useful_chunks(
    chunks: list[RetrievedChunk],
    useful_ids: list[str],
) -> list[RetrievedChunk]:
    """Filters chunks to keep only those identified as useful by the evaluator."""
    if not useful_ids:
        return chunks

    useful = set(useful_ids)

    return [chunk for chunk in chunks if chunk.chunk_id in useful]
