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


def find_by_event_type(
    session: Session,
    event_type: str,
) -> list[AuditEvent]:
    """Finds audit events by event type ordered by creation timestamp descending."""
    from sqlalchemy import select

    return list(
        session.scalars(
            select(AuditEvent)
            .where(AuditEvent.event_type == event_type)
            .order_by(AuditEvent.created_at.desc())
        ).all()
    )


def find_recent_audit_events(
    session: Session,
    limit: int = 50,
    event_type: str | None = None,
) -> list[AuditEvent]:
    """Finds recent audit events ordered by creation timestamp descending."""
    from sqlalchemy import select

    stmt = select(AuditEvent)
    if event_type is not None:
        stmt = stmt.where(AuditEvent.event_type == event_type)

    return list(
        session.scalars(
            stmt.order_by(AuditEvent.created_at.desc()).limit(limit)
        ).all()
    )
