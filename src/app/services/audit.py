from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.audit.events import AuditEventType
from app.db.repositories.audit import record_audit_event
from kit.databases.session import SessionFactory


class AuditService:
    """Service providing isolated, committed transactions for denial audits."""

    def __init__(
        self,
        session_factory: Callable[[], Session] | None = None,
    ) -> None:
        self.session_factory = session_factory or SessionFactory

    def record_denied_action(
        self,
        *,
        actor: str,
        action: str,
        entity_id: str | None,
        details: dict[str, Any],
    ) -> None:
        """Records a denied action in a separate, isolated, committed transaction."""
        with self.session_factory() as session:
            try:
                record_audit_event(
                    session=session,
                    event_type=AuditEventType.ACTION_EXECUTION_DENIED,
                    actor=actor,
                    entity_type="action",
                    entity_id=entity_id or action,
                    details=details,
                )
                session.commit()
            except Exception:
                session.rollback()
                raise
