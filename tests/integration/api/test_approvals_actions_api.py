from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from app.db import Account, Base, Customer
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
            select(Customer).where(Customer.customer_id == "CUST-API-1")
        )
        if not cust:
            cust = Customer(
                customer_id="CUST-API-1",
                name="API Test Customer",
                email="api@example.com",
                country="US",
                created_at=datetime.now(UTC),
            )
            session.add(cust)
            session.flush()

        acc = session.scalar(
            select(Account).where(Account.account_id == "ACC-API-1001")
        )
        if not acc:
            acc = Account(
                account_id="ACC-API-1001",
                customer_id=cust.id,
                account_type="checking",
                balance=Decimal("500.00"),
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
def test_approvals_and_actions_api_lifecycle(client):
    # 1. Propose action
    prop_res = client.post(
        "/api/v1/actions/propose",
        json={
            "action": "freeze_account",
            "account_id": "ACC-API-1001",
            "reason": "Suspicious large transfer burst.",
        },
    )
    assert prop_res.status_code == 200
    approval = prop_res.json()
    approval_id = approval["approval_id"]
    assert approval["status"] == "pending"
    assert "X-Request-ID" in prop_res.headers

    # 2. Inspect approval
    get_res = client.get(f"/api/v1/approvals/{approval_id}")
    assert get_res.status_code == 200
    assert get_res.json()["approval_id"] == approval_id

    # 3. Approve
    app_res = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        json={
            "actor": "compliance_lead@example.com",
            "reason": "Validated suspicious indicators.",
        },
    )
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "approved"

    # 4. Execute action
    exec_res = client.post(
        "/api/v1/actions/execute",
        json={
            "action": "freeze_account",
            "account_id": "ACC-API-1001",
            "approval_id": approval_id,
            "executed_by": "compliance_lead@example.com",
        },
    )
    assert exec_res.status_code == 200
    assert exec_res.json()["success"] is True

    # 5. Re-executing same single-use approval must fail with 403
    reexec_res = client.post(
        "/api/v1/actions/execute",
        json={
            "action": "freeze_account",
            "account_id": "ACC-API-1001",
            "approval_id": approval_id,
            "executed_by": "compliance_lead@example.com",
        },
    )
    assert reexec_res.status_code == 403


@pytest.mark.integration
def test_approval_not_found_returns_404(client):
    res = client.get("/api/v1/approvals/non-existent-approval-xyz")
    assert res.status_code == 404
    data = res.json()
    assert data["error"] == "resource_not_found"
    assert "request_id" in data
