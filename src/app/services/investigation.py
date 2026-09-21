from langchain_core.messages import (
    HumanMessage,
)

from app.api.schemas.investigations import (
    InvestigationResponse,
)


class InvestigationService:
    def __init__(
        self,
        graph,
    ) -> None:
        self._graph = graph

    async def investigate(
        self,
        *,
        question: str,
        thread_id: str,
    ) -> InvestigationResponse:
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        result = await self._graph.ainvoke(
            {
                "question": question,
                "messages": [HumanMessage(content=question)],
            },
            config=config,
        )

        return InvestigationResponse(
            thread_id=thread_id,
            plan=result.get("plan"),
            report=result.get("report"),
            sql_analysis=result.get("sql_analysis"),
            data_analysis=result.get("data_analysis"),
            policy_analysis=result.get("policy_analysis"),
            risk_analysis=result.get("risk_analysis"),
        )
