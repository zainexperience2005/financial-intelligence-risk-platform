import os
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from app.actions.freeze_account import freeze_account
from app.db.models import Account, AuditEvent, Base, Customer
from app.schemas import ProposedAction
from app.services.approvals import (
    approve_action,
    request_action_approval,
)
from kit.databases.session import SessionFactory


@pytest.fixture(autouse=True)
def setup_test_db():
    test_db_url = os.environ.get("TEST_DATABASE_URL")
    if test_db_url:
        engine = create_engine(test_db_url)
    else:
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
            select(Customer).where(Customer.customer_id == "CUST-001")
        )
        if not cust:
            cust = Customer(
                customer_id="CUST-001",
                name="Test Customer",
                email="test@example.com",
                country="US",
                created_at=datetime.now(UTC),
            )
            session.add(cust)
            session.flush()

        acc = session.scalar(select(Account).where(Account.account_id == "ACC-1001"))
        if not acc:
            acc = Account(
                account_id="ACC-1001",
                customer_id=cust.id,
                account_type="checking",
                balance=Decimal("1000.00"),
                currency="USD",
                status="active",
                created_at=datetime.now(UTC),
            )
            session.add(acc)
            session.commit()

    yield engine

    if original_bind:
        SessionFactory.configure(bind=original_bind)
    engine.dispose()


@pytest.mark.integration
def test_freeze_without_approval_fails() -> None:
    result = freeze_account(
        account_id="ACC-1001",
        approval_id="fake-approval",
        actor="analyst@example.com",
    )

    assert result.success is False
    assert result.message == "Valid approval is required."


@pytest.mark.integration
def test_pending_approval_cannot_execute() -> None:
    approval = request_action_approval(
        ProposedAction(
            action="freeze_account",
            account_id="ACC-1001",
            reason="Risk investigation.",
        )
    )

    result = freeze_account(
        account_id="ACC-1001",
        approval_id=approval.approval_id,
        actor="analyst@example.com",
    )

    assert result.success is False
    assert result.message == "Action has not been approved."


@pytest.mark.integration
def test_approval_cannot_be_used_for_other_account() -> None:
    approval = request_action_approval(
        ProposedAction(
            action="freeze_account",
            account_id="ACC-1001",
            reason="Risk investigation.",
        )
    )

    approve_action(
        approval_id=approval.approval_id,
        decided_by="officer@example.com",
    )

    result = freeze_account(
        account_id="ACC-9999",
        approval_id=approval.approval_id,
        actor="analyst@example.com",
    )

    assert result.success is False
    assert result.message == "Approval does not authorize this account."


@pytest.mark.integration
def test_approved_action_executes_and_records_audit() -> None:
    # Ensure ACC-1001 exists and reset to active for test reproducibility
    with SessionFactory() as session:
        account = session.scalar(
            select(Account).where(Account.account_id == "ACC-1001")
        )
        if account:
            account.status = "active"
            session.commit()

    approval = request_action_approval(
        ProposedAction(
            action="freeze_account",
            account_id="ACC-1001",
            reason="High risk fraud alert.",
        )
    )

    approve_action(
        approval_id=approval.approval_id,
        decided_by="compliance@example.com",
        reason="Evidence verified.",
    )

    result = freeze_account(
        account_id="ACC-1001",
        approval_id=approval.approval_id,
        actor="system_agent",
    )

    assert result.success is True
    assert result.message == "Account ACC-1001 was frozen."

    # Verify PostgreSQL account status changed
    with SessionFactory() as session:
        updated_account = session.scalar(
            select(Account).where(Account.account_id == "ACC-1001")
        )
        assert updated_account is not None
        assert updated_account.status == "frozen"

        # Verify audit event in PostgreSQL
        audit_event = session.scalar(
            select(AuditEvent)
            .where(
                AuditEvent.entity_type == "account",
                AuditEvent.entity_id == "ACC-1001",
                AuditEvent.event_type == "action_executed",
            )
            .order_by(AuditEvent.created_at.desc())
        )
        assert audit_event is not None
        assert audit_event.actor == "system_agent"
        assert audit_event.details["action"] == "freeze_account"
        assert audit_event.details["new_status"] == "frozen"


@pytest.mark.integration
def test_approval_is_single_use() -> None:
    # Reset ACC-1001 status
    with SessionFactory() as session:
        account = session.scalar(
            select(Account).where(Account.account_id == "ACC-1001")
        )
        if account:
            account.status = "active"
            session.commit()

    approval = request_action_approval(
        ProposedAction(
            action="freeze_account",
            account_id="ACC-1001",
            reason="Testing idempotency.",
        )
    )

    approve_action(
        approval_id=approval.approval_id,
        decided_by="officer@example.com",
    )

    first = freeze_account(
        account_id="ACC-1001",
        approval_id=approval.approval_id,
        actor="analyst@example.com",
    )

    second = freeze_account(
        account_id="ACC-1001",
        approval_id=approval.approval_id,
        actor="analyst@example.com",
    )

    assert first.success is True
    assert second.success is False
    assert second.message == "Action has not been approved."
