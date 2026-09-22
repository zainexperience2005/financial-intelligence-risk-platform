"""Grant SELECT privileges to the financial_reader role.

Must be run AFTER 'alembic upgrade head' has created the tables.

This script is idempotent: PostgreSQL GRANT is a no-op if the privilege
already exists.

Usage:
    python scripts/setup_readonly_role.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)


# Tables the read-only analyst role may SELECT from.
# approval_requests and audit_events are intentionally excluded —
# they must not be readable through the model-generated SQL path.
_READABLE_TABLES = [
    "customers",
    "accounts",
    "transactions",
]

_ROLE = "financial_reader"


def main() -> int:
    from sqlalchemy import text

    from kit.databases.engine import create_database_engine

    engine = create_database_engine()

    with engine.begin() as conn:
        # Connect privilege on the database
        db_name_row = conn.execute(text("SELECT current_database()")).scalar()
        conn.execute(
            text(
                f"GRANT CONNECT ON DATABASE {db_name_row} TO {_ROLE}"  # noqa: S608
            )
        )

        # Usage on the public schema
        conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {_ROLE}"))

        # SELECT on each permitted table
        for table in _READABLE_TABLES:
            conn.execute(
                text(f"GRANT SELECT ON TABLE {table} TO {_ROLE}")  # noqa: S608
            )
            print(f"[OK] GRANT SELECT ON {table} TO {_ROLE}")

    print(
        f"\nRead-only role '{_ROLE}' now has SELECT on: "
        + ", ".join(_READABLE_TABLES)
    )
    print(
        "Note: approval_requests and audit_events are intentionally "
        "excluded from the read-only role."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
