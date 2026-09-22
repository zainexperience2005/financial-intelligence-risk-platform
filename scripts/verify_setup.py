"""Environment verification script for the Financial Intelligence & Risk Platform.

Run after completing all setup steps to confirm the environment is ready:

    python scripts/verify_setup.py

Each check prints [OK] <name> on success or [FAIL] <name>: <message> on failure,
with a remediation hint. Exits 0 if all pass, 1 if any fail.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from repo root without installing the package
_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_postgresql() -> None:
    """Verify PostgreSQL is reachable via the application write connection."""
    from sqlalchemy import text

    from kit.databases.session import SessionFactory

    with SessionFactory() as session:
        session.execute(text("SELECT 1"))

    print("[OK] PostgreSQL (write connection)")


def check_migrations() -> None:
    """Verify Alembic migration state table exists and has been applied."""
    from sqlalchemy import inspect, text

    from kit.databases.engine import create_database_engine

    engine = create_database_engine()
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "alembic_version" not in tables:
        raise RuntimeError(
            "alembic_version table is missing.\n"
            "  Run: alembic upgrade head"
        )

    with engine.connect() as conn:
        row = conn.execute(text("SELECT version_num FROM alembic_version")).first()
        if row is None:
            raise RuntimeError(
                "No migration has been applied.\n"
                "  Run: alembic upgrade head"
            )

    print(f"[OK] Database migrations (revision: {row[0]})")


def check_schema() -> None:
    """Verify all required financial tables exist."""
    from sqlalchemy import inspect

    from kit.databases.engine import create_database_engine

    inspector = inspect(create_database_engine())
    existing = set(inspector.get_table_names())

    required = {
        "customers",
        "accounts",
        "transactions",
        "approval_requests",
        "audit_events",
    }
    missing = required - existing

    if missing:
        raise RuntimeError(
            "Missing database tables: "
            + ", ".join(sorted(missing))
            + "\n  Run: alembic upgrade head"
        )

    print("[OK] Financial schema (all tables present)")


def check_seed_data() -> None:
    """Verify synthetic financial data has been seeded."""
    from sqlalchemy import func, select

    from app.db.models import Account, Customer, Transaction
    from kit.databases.session import SessionFactory

    with SessionFactory() as session:
        n_customers = session.scalar(select(func.count(Customer.id))) or 0
        n_accounts = session.scalar(select(func.count(Account.id))) or 0
        n_transactions = session.scalar(select(func.count(Transaction.id))) or 0

    if n_customers == 0 or n_accounts == 0 or n_transactions == 0:
        raise RuntimeError(
            f"Synthetic data is missing "
            f"(customers={n_customers}, accounts={n_accounts}, "
            f"transactions={n_transactions}).\n"
            "  Run: python scripts/seed_database.py"
        )

    print(
        f"[OK] Synthetic data "
        f"({n_customers} customers, {n_accounts} accounts, "
        f"{n_transactions} transactions)"
    )


def check_readonly_role() -> None:
    """Verify the financial_reader role can connect and read data."""
    from sqlalchemy import create_engine, text

    from kit.config import get_settings

    settings = get_settings()
    ro_url = settings.readonly_database_url

    try:
        engine = create_engine(ro_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise RuntimeError(
            f"Read-only role is not accessible: {exc}\n"
            "  Run: python scripts/setup_readonly_role.py\n"
            "  Then verify READONLY_DATABASE_URL in .env"
        ) from exc

    print("[OK] Read-only database role (financial_reader)")


def check_qdrant() -> None:
    """Verify Qdrant is reachable."""
    from qdrant_client import QdrantClient

    from kit.config import get_settings

    settings = get_settings()
    api_key = getattr(settings, "qdrant_api_key", None)
    client = QdrantClient(url=settings.qdrant_url, api_key=api_key)
    client.get_collections()

    print("[OK] Qdrant")


def check_policy_collection() -> None:
    """Verify the financial_policies Qdrant collection exists and has vectors."""
    from qdrant_client import QdrantClient

    from kit.config import get_settings

    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url)

    existing = {c.name for c in client.get_collections().collections}

    if settings.qdrant_collection not in existing:
        raise RuntimeError(
            f"Qdrant collection '{settings.qdrant_collection}' is missing.\n"
            "  Run: python scripts/index_policies.py"
        )

    info = client.get_collection(settings.qdrant_collection)
    count = info.points_count or 0

    if count == 0:
        raise RuntimeError(
            f"Qdrant collection '{settings.qdrant_collection}' exists but has "
            "no vectors.\n"
            "  Run: python scripts/index_policies.py"
        )

    print(f"[OK] Policy collection '{settings.qdrant_collection}' ({count} vectors)")


def check_memory_collection() -> None:
    """Verify the financial_memory Qdrant collection exists."""
    from qdrant_client import QdrantClient

    from kit.config import get_settings

    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url)

    existing = {c.name for c in client.get_collections().collections}

    if settings.memory_qdrant_collection not in existing:
        raise RuntimeError(
            f"Qdrant collection '{settings.memory_qdrant_collection}' is missing.\n"
            "  Run: python scripts/setup_memory_store.py"
        )

    print(f"[OK] Memory collection '{settings.memory_qdrant_collection}'")


def check_checkpoints() -> None:
    """Verify LangGraph checkpoint tables are initialized."""
    from sqlalchemy import create_engine, inspect

    from kit.config import get_settings

    settings = get_settings()

    # Normalise the checkpoint URL scheme: LangGraph uses plain postgresql://
    # but SQLAlchemy needs the psycopg (v3) dialect explicitly.
    cp_url = settings.checkpoint_database_url
    if cp_url.startswith("postgresql://"):
        cp_url = cp_url.replace("postgresql://", "postgresql+psycopg://", 1)

    try:
        engine = create_engine(cp_url, pool_pre_ping=True)
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        checkpoint_tables = {"checkpoints", "checkpoint_writes", "checkpoint_blobs"}
        found = checkpoint_tables & table_names

        if not found:
            raise RuntimeError(
                "LangGraph checkpoint tables are missing.\n"
                "  Run: python scripts/setup_checkpoints.py"
            )

        print(f"[OK] LangGraph checkpoints ({len(found)} tables present)")
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(
            f"Could not verify checkpoint storage: {exc}\n"
            "  Run: python scripts/setup_checkpoints.py"
        ) from exc


def check_llm_config() -> None:
    """Verify the LLM API key is configured (no paid call)."""
    from kit.config import get_settings

    settings = get_settings()

    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured.\n"
            "  Set it in .env: OPENAI_API_KEY=sk-..."
        )

    print("[OK] LLM configuration (OPENAI_API_KEY present)")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

CHECKS = [
    check_postgresql,
    check_migrations,
    check_schema,
    check_seed_data,
    check_readonly_role,
    check_qdrant,
    check_policy_collection,
    check_memory_collection,
    check_checkpoints,
    check_llm_config,
]


def main() -> int:
    failures: list[tuple[str, str]] = []

    for check in CHECKS:
        try:
            check()
        except Exception as exc:  # noqa: BLE001
            name = check.__name__.removeprefix("check_").replace("_", " ")
            failures.append((name, str(exc)))
            print(f"[FAIL] {name}: {exc}")

    if failures:
        print(f"\nSetup verification failed ({len(failures)} check(s)).")
        print("Fix the issues above and re-run: python scripts/verify_setup.py")
        return 1

    print(
        f"\nEnvironment verification passed. "
        f"All {len(CHECKS)} checks succeeded."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
