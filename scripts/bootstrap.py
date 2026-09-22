"""Infrastructure bootstrap for the Financial Intelligence & Risk Platform.

This script initialises the persistent infrastructure layer. It is safe to
run multiple times — all operations are idempotent.

What this does:
  1. Applies pending Alembic database migrations
  2. Initialises LangGraph checkpoint tables
  3. Creates Qdrant vector collections (if absent)

What this does NOT do (run separately to keep control explicit):
  - Seed synthetic financial data  →  python scripts/seed_database.py
  - Index policy documents         →  python scripts/index_policies.py
  - Grant read-only DB privileges  →  python scripts/setup_readonly_role.py
  - Verify the full environment    →  python scripts/verify_setup.py

Usage:
    python scripts/bootstrap.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)


# ---------------------------------------------------------------------------
# Known embedding dimension for text-embedding-3-small.
# Using a constant avoids making a paid OpenAI call during bootstrap.
# ---------------------------------------------------------------------------
_EMBEDDING_DIMENSION = 1536


def create_database_tables() -> None:
    """Apply pending Alembic migrations to the application database."""
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(
        str(Path(__file__).resolve().parent.parent / "alembic.ini")
    )
    command.upgrade(alembic_cfg, "head")
    print("[OK] Database migrations applied (alembic upgrade head).")


def setup_checkpoints() -> None:
    """Initialise LangGraph checkpoint tables in PostgreSQL."""
    try:
        from langgraph.checkpoint.postgres import PostgresSaver

        from kit.config import get_settings

        settings = get_settings()
        with PostgresSaver.from_conn_string(
            settings.checkpoint_database_url
        ) as checkpointer:
            checkpointer.setup()
        print("[OK] LangGraph checkpoint tables initialised.")
    except Exception as exc:
        print(f"[WARN] Checkpoint setup skipped or failed: {exc}")
        print("       Run manually: python scripts/setup_checkpoints.py")


def setup_vector_collections() -> None:
    """Create Qdrant vector collections if they do not already exist.

    Uses a fixed embedding dimension to avoid making a paid API call
    during infrastructure bootstrap.
    """
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        from kit.config import get_settings

        settings = get_settings()
        client = QdrantClient(url=settings.qdrant_url)

        existing = {item.name for item in client.get_collections().collections}

        collections = [
            settings.qdrant_collection,
            settings.memory_qdrant_collection,
        ]

        for coll in collections:
            if coll not in existing:
                client.create_collection(
                    collection_name=coll,
                    vectors_config=VectorParams(
                        size=_EMBEDDING_DIMENSION,
                        distance=Distance.COSINE,
                    ),
                )
                print(f"[OK] Created Qdrant collection: {coll}")
            else:
                print(f"[OK] Qdrant collection already exists: {coll}")

    except Exception as exc:
        print(f"[WARN] Qdrant setup skipped or failed: {exc}")
        print("       Ensure Qdrant is running: docker compose up -d qdrant")


def main() -> None:
    print("=" * 60)
    print("Financial Intelligence & Risk Platform — Bootstrap")
    print("=" * 60)

    create_database_tables()
    setup_checkpoints()
    setup_vector_collections()

    print()
    print("Bootstrap complete. Next steps:")
    print("  python scripts/setup_readonly_role.py  # grant SELECT to reader role")
    print("  python scripts/seed_database.py        # seed synthetic demo data")
    print("  python scripts/index_policies.py       # index policy documents")
    print("  python scripts/verify_setup.py         # verify everything is ready")


if __name__ == "__main__":
    main()
