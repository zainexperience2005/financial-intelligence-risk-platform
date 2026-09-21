"""Corrective Policy Retrieval Tool (CRAG) for the Policy Agent.

Adapts the reusable kit CRAG pipeline into an app-level tool.
Evaluates evidence relevance and performs bounded correction before returning results.
"""

from pydantic import BaseModel, Field

from kit.crag import corrective_retrieve
from kit.tools import BaseTool, ToolResult


class CorrectivePolicyRetrievalInput(BaseModel):
    query: str = Field(
        min_length=1,
        description="Focused query describing policy evidence required.",
    )

    k: int = Field(
        default=4,
        ge=1,
        le=8,
        description="Maximum number of policy chunks to retrieve per search.",
    )


class CorrectivePolicyRetrievalTool(BaseTool[CorrectivePolicyRetrievalInput]):
    name = "corrective_policy_retrieval"

    description = (
        "Retrieve financial policy evidence, "
        "evaluate its relevance, and perform one "
        "corrective retrieval when necessary."
    )

    input_schema = CorrectivePolicyRetrievalInput

    def execute(
        self,
        input_data: CorrectivePolicyRetrievalInput,
    ) -> ToolResult:
        try:
            result = corrective_retrieve(
                query=input_data.query,
                k=input_data.k,
            )

            return ToolResult(
                success=True,
                data={
                    "answerable": result.answerable,
                    "correction_used": (result.correction_used),
                    "retrieval_attempts": (result.retrieval_attempts),
                    "original_query": (result.original_query),
                    "final_query": (result.final_query),
                    "relevance": (result.final_evaluation.relevance),
                    "reason": (result.final_evaluation.reason),
                    "chunks": [chunk.model_dump() for chunk in result.chunks],
                },
            )

        except Exception:
            return ToolResult(
                success=False,
                error=("Corrective policy retrieval failed."),
            )
