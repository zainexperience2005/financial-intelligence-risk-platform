from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.pool import StaticPool

from app.db import Account, AuditEvent, Base, Customer
from kit.config import get_settings
from kit.databases import create_database_engine
from kit.databases.session import SessionFactory


@pytest.fixture(autouse=True)
def setup_db():
    settings = get_settings()
    if settings.database_url.startswith("sqlite"):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_database_engine()

    Base.metadata.create_all(bind=engine)
    original_bind = SessionFactory.kw.get("bind")
    SessionFactory.configure(bind=engine)

    yield engine

    if original_bind:
        SessionFactory.configure(bind=original_bind)
    engine.dispose()


@pytest.mark.integration
def test_database_connection(setup_db) -> None:
    engine = setup_db
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


@pytest.mark.integration
def test_database_schema_and_tables(setup_db) -> None:
    engine = setup_db
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    expected_tables = {
        "accounts",
        "customers",
        "transactions",
        "approval_requests",
        "audit_events",
    }
    assert expected_tables.issubset(table_names)


@pytest.mark.integration
def test_account_and_audit_persistence(setup_db) -> None:
    with SessionFactory() as session:
        cust = Customer(
            customer_id="CUST-INTEG-DB-1",
            name="Integ DB Customer",
            email="db-integ@example.com",
            country="US",
            created_at=datetime.now(UTC),
        )
        session.add(cust)
        session.flush()

        acc = Account(
            account_id="ACC-INTEG-DB-1",
            customer_id=cust.id,
            account_type="checking",
            balance=Decimal("2500.00"),
            currency="USD",
            status="active",
            created_at=datetime.now(UTC),
        )
        session.add(acc)

        audit = AuditEvent(
            event_type="test_db_event",
            actor="test_runner",
            entity_type="account",
            entity_id="ACC-INTEG-DB-1",
            details={"status": "initial_seed"},
            created_at=datetime.now(UTC),
        )
        session.add(audit)
        session.commit()

    with SessionFactory() as session:
        retrieved_acc = session.scalar(
            select(Account).where(Account.account_id == "ACC-INTEG-DB-1")
        )
        assert retrieved_acc is not None
        assert retrieved_acc.balance == Decimal("2500.00")

        retrieved_audit = session.scalar(
            select(AuditEvent).where(AuditEvent.entity_id == "ACC-INTEG-DB-1")
        )
        assert retrieved_audit is not None
        assert retrieved_audit.actor == "test_runner"
