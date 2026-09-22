"""Fixtures for deterministic and offline security regression testing."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from app.db.models import Account, Base, Customer
from app.services.actions import ActionService
from kit.databases.session import SessionFactory


@pytest.fixture(autouse=True)
def setup_security_db():
    """Configure isolated SQLite in-memory database with test accounts."""
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
            select(Customer).where(Customer.customer_id == "CUST-SEC-001")
        )
        if not cust:
            cust = Customer(
                customer_id="CUST-SEC-001",
                name="Security Test User",
                email="security@example.com",
                country="Pakistan",
                created_at=datetime.now(UTC),
            )
            session.add(cust)
            session.flush()

        acc1 = session.scalar(select(Account).where(Account.account_id == "ACC-1001"))
        if not acc1:
            acc1 = Account(
                account_id="ACC-1001",
                customer_id=cust.id,
                account_type="current",
                balance=Decimal("500000.00"),
                currency="PKR",
                status="active",
                created_at=datetime.now(UTC),
            )
            session.add(acc1)

        acc2 = session.scalar(select(Account).where(Account.account_id == "ACC-9999"))
        if not acc2:
            acc2 = Account(
                account_id="ACC-9999",
                customer_id=cust.id,
                account_type="current",
                balance=Decimal("250000.00"),
                currency="PKR",
                status="active",
                created_at=datetime.now(UTC),
            )
            session.add(acc2)

        session.commit()

    yield

    if original_bind:
        SessionFactory.configure(bind=original_bind)


@pytest.fixture
def action_service():
    """Provide ActionService instance."""
    return ActionService()
