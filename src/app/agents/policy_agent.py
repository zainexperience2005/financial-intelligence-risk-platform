"""Policy Agent implementation for financial risk policy retrieval and synthesis.

Role:
Identifies and grounds financial investigations in official bank policies
(e.g., transaction monitoring rules, account freezing approvals,
high-value transfer thresholds). Uses Corrective Policy Retrieval (CRAG)
to avoid hallucinations and verify answerability.
"""

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.prompts.policy_agent import (
    POLICY_AGENT_SYSTEM_PROMPT,
)
from app.schemas import (
    PolicyAnalysisResult,
    PolicyCitation,
)
from app.security.pii import prepare_model_evidence
from app.tools import CorrectivePolicyRetrievalTool
from kit.llms import create_chat_model
from kit.security.pii import mask_free_text
from kit.tools.adapters import to_langchain_tool

# Hard limit on retrieval attempts to prevent infinite agent loop execution
MAX_POLICY_TOOL_CALLS = 2


def run_policy_agent(
    question: str,
) -> PolicyAnalysisResult:
    """Runs the Policy Agent to find and cite relevant financial policies.

    Args:
        question: User inquiry or risk investigation topic.

    Returns:
        PolicyAnalysisResult with synthesized policy advice, citation sources,
        and CRAG evaluation metadata (relevance, correction_used, attempts).
    """
    retrieval_tool = to_langchain_tool(CorrectivePolicyRetrievalTool())

    model = create_chat_model().bind_tools([retrieval_tool])

    messages: list[BaseMessage] = [
        SystemMessage(content=POLICY_AGENT_SYSTEM_PROMPT),
        HumanMessage(content=mask_free_text(question)),
    ]

    retrieved_chunks: list[dict] = []
    last_retrieval_data: dict | None = None
    tool_calls = 0

    for _ in range(MAX_POLICY_TOOL_CALLS + 1):
        response = model.invoke(messages)
        messages.append(response)

        # If model did not request further tools, finalize and format the answer
        if not response.tool_calls:
            citations = []

            seen = set()

            for chunk in retrieved_chunks:
                key = (
                    chunk.get("source"),
                    chunk.get("chunk_id"),
                )

                if key in seen:
                    continue

                seen.add(key)

                citations.append(
                    PolicyCitation(
                        source=chunk.get(
                            "source",
                            "unknown",
                        ),
                        chunk_id=chunk.get("chunk_id"),
                    )
                )

            return PolicyAnalysisResult(
                summary=str(response.content),
                grounded=bool(
                    last_retrieval_data
                    and last_retrieval_data.get("answerable")
                    and retrieved_chunks
                ),
                citations=citations,
                retrieved_chunk_count=len(retrieved_chunks),
                retrieval_relevance=(
                    last_retrieval_data.get("relevance")
                    if last_retrieval_data
                    else None
                ),
                correction_used=(
                    bool(last_retrieval_data.get("correction_used"))
                    if last_retrieval_data
                    else False
                ),
                retrieval_attempts=(
                    int(last_retrieval_data.get("retrieval_attempts", 0))
                    if last_retrieval_data
                    else 0
                ),
            )

        for tool_call in response.tool_calls:
            if tool_calls >= MAX_POLICY_TOOL_CALLS:
                return PolicyAnalysisResult(
                    summary=("Policy retrieval budget was exhausted."),
                    grounded=False,
                )

            tool_calls += 1

            observation = retrieval_tool.invoke(tool_call["args"])

            if isinstance(observation, dict) and observation.get("success"):
                retrieval_data = observation.get(
                    "data",
                    {},
                )
                last_retrieval_data = retrieval_data

                retrieved_chunks.extend(
                    retrieval_data.get(
                        "chunks",
                        [],
                    )
                )

            messages.append(
                ToolMessage(
                    content=mask_free_text(
                        str(
                            prepare_model_evidence(observation)
                            if isinstance(observation, dict)
                            else observation
                        )
                    ),
                    tool_call_id=tool_call["id"],
                )
            )

    return PolicyAnalysisResult(
        summary="Policy investigation stopped.",
        grounded=False,
    )
