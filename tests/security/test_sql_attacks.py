"""Red-team security tests verifying SQL injection and mutation rejection."""

import pytest

from app.tools.safe_sql import SafeSQLTool
from kit.databases.sql import SQLValidationError, validate_read_only_sql


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM transactions",
        "UPDATE accounts SET status='frozen'",
        "DROP TABLE transactions",
        "ALTER TABLE accounts ADD COLUMN hacked TEXT",
        "INSERT INTO transactions DEFAULT VALUES",
        "CREATE TABLE backdoor (id INT)",
    ],
)
def test_mutating_sql_is_rejected(sql: str):
    """Verify that any DDL or DML mutation statement raises SQLValidationError."""
    with pytest.raises(SQLValidationError):
        validate_read_only_sql(sql)


def test_multiple_statements_rejected():
    """Verify that piggybacked multi-statement attacks are rejected."""
    attack_sql = """
    SELECT * FROM transactions;
    DELETE FROM transactions;
    """
    with pytest.raises(SQLValidationError):
        validate_read_only_sql(attack_sql)


def test_disguised_cte_mutation_rejected():
    """Verify that mutations disguised within CTEs are caught."""
    cte_attack = """
    WITH wiped AS (
        DELETE FROM transactions RETURNING *
    )
    SELECT * FROM wiped;
    """
    with pytest.raises(SQLValidationError):
        validate_read_only_sql(cte_attack)


def test_safe_sql_tool_blocks_mutations_and_returns_controlled_error():
    """Verify that SafeSQLTool wraps validator rejections cleanly without executing."""
    tool = SafeSQLTool()
    result = tool.run({"query": "DROP TABLE accounts;"})

    assert result.success is False
    assert result.error is not None
    msg = result.error.message.lower()
    assert "read-only" in msg or "only select" in msg
