"""Baseline Financial Policy Retrieval Tool (Normal RAG).

Directly queries the Qdrant policy vector store for top-k chunks.
Preserved as our measurement baseline to compare against Corrective RAG (CRAG).
"""

from pydantic import BaseModel, Field

from kit.rag.retriever import retrieve_chunks
from kit.tools import BaseTool, ToolResult


class PolicyRetrievalInput(BaseModel):
    query: str = Field(
        min_length=1,
        description=(
            "A focused query describing the financial policy or rule evidence required."
        ),
    )

    k: int = Field(
        default=4,
        ge=1,
        le=8,
    )


class PolicyRetrievalTool(BaseTool[PolicyRetrievalInput]):
    name = "policy_retrieval"

    description = (
        "Retrieve relevant financial policy evidence "
        "from the approved policy knowledge base."
    )

    input_schema = PolicyRetrievalInput

    def execute(
        self,
        input_data: PolicyRetrievalInput,
    ) -> ToolResult:
        try:
            chunks = retrieve_chunks(
                query=input_data.query,
                k=input_data.k,
            )

            return ToolResult(
                success=True,
                data=[chunk.model_dump() for chunk in chunks],
            )

        except Exception:
            return ToolResult(
                success=False,
                error="Policy retrieval failed.",
            )
