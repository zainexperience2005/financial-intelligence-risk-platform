from kit.approvals.models import (
    ApprovalDecision,
    ApprovalRequest,
)


class ApprovalStore:
    def __init__(self) -> None:
        self._requests: dict[
            str,
            ApprovalRequest,
        ] = {}

        self._decisions: dict[
            str,
            ApprovalDecision,
        ] = {}

    def create(
        self,
        request: ApprovalRequest,
    ) -> ApprovalRequest:
        self._requests[request.approval_id] = request

        return request

    def get(
        self,
        approval_id: str,
    ) -> ApprovalRequest | None:
        return self._requests.get(approval_id)

    def decide(
        self,
        decision: ApprovalDecision,
    ) -> ApprovalRequest:
        request = self.get(decision.approval_id)

        if request is None:
            raise ValueError("Approval request not found.")

        if request.status != "pending":
            raise ValueError("Approval request has already been decided.")

        request.status = decision.decision

        self._decisions[decision.approval_id] = decision

        return request

    def mark_executed(
        self,
        approval_id: str,
    ) -> None:
        request = self.get(approval_id)

        if request is None:
            raise ValueError("Approval request not found.")

        if request.status != "approved":
            raise ValueError("Only approved requests can be marked as executed.")

        request.status = "executed"
