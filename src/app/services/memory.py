from typing import Any

from app.memory.builders import build_investigation_memory
from app.memory.policy import (
    INVESTIGATION_MEMORY_RETENTION_DAYS,
    should_store_investigation,
)
from app.schemas.memory_context import InvestigationMemoryContext
from kit.context.models import ContextCategory, ContextItem
from kit.memory.models import MemoryRecord, MemorySearchResult
from kit.memory.service import MemoryService as KitMemoryService


class AppMemoryService:
    """Application service coordinating long-term memory operations."""


    def __init__(
        self,
        kit_service: KitMemoryService | None = None,
    ) -> None:
        self._kit_service = kit_service or KitMemoryService()

    def remember(
        self,
        *,
        content: str,
        memory_type: str = "investigation",
        retention_days: int = INVESTIGATION_MEMORY_RETENTION_DAYS,
        metadata: dict[str, str] | None = None,
    ) -> MemoryRecord:
        """Explicitly stores content in long-term memory."""
        return self._kit_service.remember(
            content=content,
            memory_type=memory_type,
            retention_days=retention_days,
            metadata=metadata or {},
        )


    def remember_investigation(
        *,
        self,
        transaction_id: str | None,
        risk_assessment: Any,
        policy_sources: list[str],
        report_available: bool = True,
    ) -> MemoryRecord | None:
        """Stores an investigation if it satisfies persistence criteria."""
        decision = should_store_investigation(
            transaction_id=transaction_id,
            report_available=report_available,
            risk_available=risk_assessment is not None,
        )

        if not decision.should_store or transaction_id is None:
            return None

        content, metadata = build_investigation_memory(
            transaction_id=transaction_id,
            risk_assessment=risk_assessment,
            policy_sources=policy_sources,
        )

        return self._kit_service.remember(
            content=content,
            memory_type="investigation",
            retention_days=INVESTIGATION_MEMORY_RETENTION_DAYS,
            metadata=metadata,
        )

    def recall(
        self,
        query: str,
        *,
        k: int = 5,
        transaction_id: str | None = None,
    ) -> list[InvestigationMemoryContext]:
        """Searches long-term memories relevant to query or transaction ID."""

        raw_results: list[MemorySearchResult] = self._kit_service.recall(
            query,
            k=k,
        )

        contexts: list[InvestigationMemoryContext] = []
        for r in raw_results:
            tx_id = r.metadata.get("transaction_id")
            # If transaction_id is provided, filter for exact match
            if transaction_id and tx_id != transaction_id:
                continue

            contexts.append(
                InvestigationMemoryContext(
                    memory_id=r.memory_id,
                    content=r.content,
                    transaction_id=tx_id,
                    ruleset_version=r.metadata.get("ruleset_version"),
                    relevance_score=r.score,
                )
            )

        return contexts

    def forget(
        self,
        memory_id: str,
    ) -> bool:
        """Deletes a long-term memory record by ID."""
        try:
            self._kit_service.forget(memory_id)
            return True
        except Exception:
            return False

    @staticmethod
    def to_context_item(
        memory: InvestigationMemoryContext,
    ) -> ContextItem:
        """Converts an investigation memory context into a budgeted ContextItem."""
        return ContextItem(
            content=memory.content,
            category=ContextCategory.MEMORY,
            priority=40,
            required=False,
            source_id=memory.memory_id,
        )


memory_service = AppMemoryService()


def remember_investigation(
    *,
    transaction_id: str,
    report: Any = None,
    risk_analysis: Any = None,
) -> str | None:
    """Stores a formatted investigation summary in long-term memory."""
    risk_level = "unknown"
    risk_score = 0
    assessment = getattr(risk_analysis, "assessment", None) if risk_analysis else None
    if assessment:
        risk_level = getattr(assessment, "level", "unknown")
        risk_score = getattr(assessment, "score", 0)


    content = (
        f"Investigation for {transaction_id}. "
        f"Risk level: {risk_level}. "
        f"Risk score: {risk_score}."
    )
    metadata = {
        "transaction_id": transaction_id,
        "source": "investigation_report",
        "risk_level": str(risk_level),
        "risk_score": str(risk_score),
    }
    record = memory_service.remember(
        content=content,
        memory_type="investigation",
        retention_days=INVESTIGATION_MEMORY_RETENTION_DAYS,
        metadata=metadata,
    )
    return getattr(record, "memory_id", None)
