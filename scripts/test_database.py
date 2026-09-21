from sqlalchemy import text

from kit.databases import create_database_engine


def main() -> None:
    engine = create_database_engine()

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        value = result.scalar_one()

        print(f"Database connection successful: {value}")


if __name__ == "__main__":
    main()
