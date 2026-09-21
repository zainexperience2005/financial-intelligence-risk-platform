from app.db import Base
from kit.databases import create_database_engine


def main() -> None:
    engine = create_database_engine()

    Base.metadata.create_all(
        bind=engine
    )

    print(
        "Financial database tables created."
    )


if __name__ == "__main__":
    main()