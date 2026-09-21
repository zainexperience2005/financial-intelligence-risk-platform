"""Infrastructure bootstrap script for initializing persistent storage and schema."""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.db.models import Base
from kit.config import get_settings
from kit.databases.engine import create_database_engine
from kit.embeddings import create_embeddings


def create_database_tables() -> None:
    settings = get_settings()
    engine = create_database_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    print("PostgreSQL tables created.")


def setup_checkpoints() -> None:
    try:
        from langgraph.checkpoint.postgres import PostgresSaver

        settings = get_settings()
        with PostgresSaver.from_conn_string(
            settings.checkpoint_database_url
        ) as checkpointer:
            checkpointer.setup()
        print("LangGraph checkpoint tables initialized.")
    except Exception as exc:
        print(f"Skipping or failed checkpoint setup: {exc}")


def setup_vector_collections() -> None:
    try:
        settings = get_settings()
        client = QdrantClient(url=settings.qdrant_url)
        embeddings = create_embeddings()
        vector_size = len(embeddings.embed_query("bootstrap check"))

        existing = {item.name for item in client.get_collections().collections}

        for coll in [settings.qdrant_collection, settings.memory_qdrant_collection]:
            if coll not in existing:
                client.create_collection(
                    collection_name=coll,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE,
                    ),
                )
                print(f"Created vector collection: {coll}")
            else:
                print(f"Vector collection already exists: {coll}")
    except Exception as exc:
        print(f"Skipping or failed vector collections setup: {exc}")


def main() -> None:
    print("Starting infrastructure bootstrap...")
    create_database_tables()
    setup_checkpoints()
    setup_vector_collections()
    print("Infrastructure bootstrap complete.")


if __name__ == "__main__":
    main()
