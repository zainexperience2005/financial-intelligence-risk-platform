from __future__ import annotations

import sys
from pathlib import Path

_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.db import Account, Customer, Transaction
from kit.databases import SessionFactory


def main() -> None:
    with SessionFactory() as session:
        existing = session.scalar(select(Customer).limit(1))

        if existing is not None:
            print("Database already contains seed data.")
            return

        now = datetime.now(UTC)

        customers = [
            Customer(
                customer_id="CUS-1001",
                name="Ali Khan",
                email="ali@example.com",
                country="Pakistan",
                created_at=now - timedelta(days=400),
            ),
            Customer(
                customer_id="CUS-1002",
                name="Sara Ahmed",
                email="sara@example.com",
                country="Pakistan",
                created_at=now - timedelta(days=250),
            ),
            Customer(
                customer_id="CUS-1003",
                name="Hamza Malik",
                email="hamza@example.com",
                country="Pakistan",
                created_at=now - timedelta(days=150),
            ),
        ]

        session.add_all(customers)
        session.flush()

        accounts = [
            Account(
                account_id="ACC-1001",
                customer_id=customers[0].id,
                account_type="current",
                balance=Decimal("450000.00"),
                currency="PKR",
                status="active",
                created_at=now - timedelta(days=390),
            ),
            Account(
                account_id="ACC-1002",
                customer_id=customers[1].id,
                account_type="savings",
                balance=Decimal("275000.00"),
                currency="PKR",
                status="active",
                created_at=now - timedelta(days=240),
            ),
            Account(
                account_id="ACC-1003",
                customer_id=customers[2].id,
                account_type="current",
                balance=Decimal("820000.00"),
                currency="PKR",
                status="active",
                created_at=now - timedelta(days=140),
            ),
        ]

        session.add_all(accounts)
        session.flush()

        transactions = [
            Transaction(
                transaction_id="TX-1001",
                account_id=accounts[0].id,
                transaction_type="card_payment",
                amount=Decimal("12500.00"),
                currency="PKR",
                status="completed",
                failure_reason=None,
                merchant_category="electronics",
                destination_country="Pakistan",
                created_at=now - timedelta(days=6),
            ),
            Transaction(
                transaction_id="TX-1002",
                account_id=accounts[0].id,
                transaction_type="card_payment",
                amount=Decimal("8500.00"),
                currency="PKR",
                status="failed",
                failure_reason="insufficient_funds",
                merchant_category="retail",
                destination_country="Pakistan",
                created_at=now - timedelta(days=5),
            ),
            Transaction(
                transaction_id="TX-1003",
                account_id=accounts[1].id,
                transaction_type="transfer",
                amount=Decimal("35000.00"),
                currency="PKR",
                status="completed",
                failure_reason=None,
                merchant_category=None,
                destination_country="Pakistan",
                created_at=now - timedelta(days=4),
            ),
            Transaction(
                transaction_id="TX-1004",
                account_id=accounts[1].id,
                transaction_type="card_payment",
                amount=Decimal("18500.00"),
                currency="PKR",
                status="failed",
                failure_reason="processor_timeout",
                merchant_category="travel",
                destination_country="Pakistan",
                created_at=now - timedelta(days=3),
            ),
            Transaction(
                transaction_id="TX-1005",
                account_id=accounts[2].id,
                transaction_type="transfer",
                amount=Decimal("450000.00"),
                currency="PKR",
                status="completed",
                failure_reason=None,
                merchant_category=None,
                destination_country="United Arab Emirates",
                created_at=now - timedelta(days=2),
            ),
            Transaction(
                transaction_id="TX-1006",
                account_id=accounts[2].id,
                transaction_type="transfer",
                amount=Decimal("475000.00"),
                currency="PKR",
                status="failed",
                failure_reason="risk_review",
                merchant_category=None,
                destination_country="United Arab Emirates",
                created_at=now - timedelta(days=1),
            ),
        ]

        session.add_all(transactions)

        session.commit()

        print(
            f"Inserted {len(customers)} customers, "
            f"{len(accounts)} accounts and "
            f"{len(transactions)} transactions."
        )


if __name__ == "__main__":
    main()
