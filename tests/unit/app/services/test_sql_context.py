from app.services.sql_context import (
    MAX_MODEL_SQL_ROWS,
    prepare_sql_rows_for_model,
)


def test_sql_rows_are_bounded():
    rows = [
        {
            "transaction_id": f"TX-{i}",
        }
        for i in range(100)
    ]

    result = prepare_sql_rows_for_model(rows)

    assert len(result["rows"]) == MAX_MODEL_SQL_ROWS
    assert result["truncated"] is True
    assert result["total_rows_received"] == 100
    assert result["returned_to_model"] == MAX_MODEL_SQL_ROWS


def test_sql_rows_not_truncated_when_under_limit():
    rows = [
        {
            "transaction_id": f"TX-{i}",
        }
        for i in range(10)
    ]

    result = prepare_sql_rows_for_model(rows)

    assert len(result["rows"]) == 10
    assert result["truncated"] is False
    assert result["total_rows_received"] == 10
    assert result["returned_to_model"] == 10
