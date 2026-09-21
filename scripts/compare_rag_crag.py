from kit.crag import corrective_retrieve
from kit.rag.retriever import retrieve_chunks


def main() -> None:
    query = "What is the policy for cryptocurrency wallet withdrawals?"

    print("\nNORMAL RAG")
    print("=" * 60)

    normal_results = retrieve_chunks(
        query,
        k=4,
    )

    for chunk in normal_results:
        print(
            chunk.source,
            chunk.chunk_id,
        )

    print("\nCRAG")
    print("=" * 60)

    crag_result = corrective_retrieve(
        query=query,
        k=4,
    )

    print(
        "Initial relevance:",
        crag_result.initial_evaluation.relevance,
    )

    print(
        "Correction used:",
        crag_result.correction_used,
    )

    print(
        "Final query:",
        crag_result.final_query,
    )

    print(
        "Final relevance:",
        crag_result.final_evaluation.relevance,
    )

    print("\nFinal evidence:")

    for chunk in crag_result.chunks:
        print(
            chunk.source,
            chunk.chunk_id,
        )


if __name__ == "__main__":
    main()
