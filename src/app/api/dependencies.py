from fastapi import Request

from app.services.actions import ActionService
from app.services.approvals import ApprovalService
from app.services.investigation import InvestigationService


def get_investigation_service(
    request: Request,
) -> InvestigationService:
    graph = getattr(
        request.app.state,
        "financial_graph",
        None,
    )
    if graph is None:
        from app.graphs.financial_graph import build_financial_graph

        graph = build_financial_graph()
    return InvestigationService(graph=graph)


def get_approval_service() -> ApprovalService:
    return ApprovalService()


def get_action_service() -> ActionService:
    return ActionService()
