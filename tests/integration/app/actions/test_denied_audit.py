from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from app.actions.freeze_account import freeze_account
from app.db import Account, AuditEvent, Base, Customer
from app.schemas import ProposedAction
from app.services.approvals import request_action_approval
from kit.databases.session import SessionFactory


@pytest.fixture(autouse=True)
def init_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    original_bind = SessionFactory.kw.get("bind")
    SessionFactory.configure(bind=engine)

    with SessionFactory() as session:
        cust = session.scalar(
            select(Customer).where(Customer.customer_id == "CUST-AUDIT-1")
        )
        if not cust:
            cust = Customer(
                customer_id="CUST-AUDIT-1",
                name="Audit Test Customer",
                email="audit@example.com",
                country="US",
                created_at=datetime.now(UTC),
            )
            session.add(cust)
            session.flush()

        acc = session.scalar(
            select(Account).where(Account.account_id == "ACC-AUDIT-1001")
        )
        if not acc:
            acc = Account(
                account_id="ACC-AUDIT-1001",
                customer_id=cust.id,
                account_type="checking",
                balance=Decimal("1000.00"),
                currency="USD",
                status="active",
                created_at=datetime.now(UTC),
            )
            session.add(acc)
            session.commit()
        else:
            acc.status = "active"
            session.commit()

    yield engine

    if original_bind:
        SessionFactory.configure(bind=original_bind)
    engine.dispose()


@pytest.mark.integration
def test_denied_attempt_is_audited():
    # 1. Blocked attempt due to invalid approval
    result = freeze_account(
        account_id="ACC-AUDIT-1001",
        approval_id="nonexistent-appr-999",
        actor="rogue_agent",
    )
    assert result.success is False

    with SessionFactory() as session:
        audit_event = session.scalar(
            select(AuditEvent)
            .where(
                AuditEvent.event_type == "action_execution_denied",
                AuditEvent.entity_id == "ACC-AUDIT-1001",
            )
            .order_by(AuditEvent.created_at.desc())
        )
        assert audit_event is not None
        assert audit_event.actor == "rogue_agent"
        assert audit_event.details["reason"] == "approval_not_found"

    # 2. Blocked attempt due to unapproved status
    prop = request_action_approval(
        ProposedAction(
            action="freeze_account",
            account_id="ACC-AUDIT-1001",
            reason="Test unapproved audit",
        )
    )
    result_pending = freeze_account(
        account_id="ACC-AUDIT-1001",
        approval_id=prop.approval_id,
        actor="premature_agent",
    )
    assert result_pending.success is False

    with SessionFactory() as session:
        audit_pending = session.scalar(
            select(AuditEvent)
            .where(
                AuditEvent.event_type == "action_execution_denied",
                AuditEvent.actor == "premature_agent",
            )
            .order_by(AuditEvent.created_at.desc())
        )
        assert audit_pending is not None
        assert audit_pending.details["reason"] == "approval_pending"
