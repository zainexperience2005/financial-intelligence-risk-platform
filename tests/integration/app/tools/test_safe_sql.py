"""PostgreSQL-specific checks use only an explicitly supplied reader URL."""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from app.tools import SafeSQLInput, SafeSQLTool

pytestmark = pytest.mark.postgres


@pytest.fixture
def sql_tool(monkeypatch):
    url = os.environ.get("TEST_READ_ONLY_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_READ_ONLY_DATABASE_URL to run PostgreSQL checks")
    engine = create_engine(url)
    monkeypatch.setattr("app.tools.safe_sql.create_database_engine", lambda **_: engine)
    yield SafeSQLTool(max_rows=2)
    engine.dispose()


def test_safe_sql_executes_limited_select(sql_tool):
    result = sql_tool.execute(
        SafeSQLInput(query="SELECT n FROM generate_series(1, 5) AS n ORDER BY n")
    )
    assert result.success, result.error
    assert result.data["rows"] == [{"n": 1}, {"n": 2}]
    assert result.data["row_count"] == 2


def test_safe_sql_rejects_delete(sql_tool):
    result = sql_tool.execute(SafeSQLInput(query="DELETE FROM transactions"))
    assert not result.success


def test_reader_has_no_public_table_mutation_privileges(sql_tool):
    with sql_tool._engine.connect() as connection:
        assert connection.scalar(
            text("SELECT NOT rolsuper FROM pg_roles WHERE rolname = current_user")
        )
        assert (
            connection.scalar(
                text("""
            SELECT count(*) FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
              AND has_table_privilege(
                current_user,
                quote_ident(table_schema) || '.' || quote_ident(table_name),
                'INSERT,UPDATE,DELETE,TRUNCATE'
              )
        """)
            )
            == 0
        )


def test_postgres_statement_timeout():
    url = os.environ.get("TEST_READ_ONLY_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_READ_ONLY_DATABASE_URL to run PostgreSQL checks")
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            connection.execute(text("SET LOCAL statement_timeout = '10ms'"))
            with pytest.raises(DBAPIError):
                connection.execute(text("SELECT pg_sleep(0.1)"))
    finally:
        engine.dispose()
