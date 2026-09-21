from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import AuditEvent


def record_audit_event(
    session: Session,
    *,
    event_type: str,
    actor: str,
    entity_type: str,
    entity_id: str,
    details: dict[str, Any],
) -> AuditEvent:
    """Records an audit event within the caller's active database transaction.

    Note: Transaction control (commit/rollback) remains the responsibility of
    the calling service layer to ensure atomic multi-table state transitions.
    """
    event = AuditEvent(
        event_type=event_type,
        actor=actor,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        created_at=datetime.now(UTC),
    )

    session.add(event)

    return event
