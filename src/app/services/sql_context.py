"""Service layer for preparing bounded SQL query results for model consumption."""

from typing import Any

# Maximum SQL result rows exposed directly to the model context window
MAX_MODEL_SQL_ROWS = 50


def prepare_sql_rows_for_model(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Slice raw SQL rows for model visibility and attach explicit truncation metadata.

    Ensures the model understands when it is observing a bounded sample rather than the
    complete dataset, preventing false assumptions during analysis.
    Aggregations should be performed by DataAnalysisTool over the full rows,
    while this function prepares the visible sample for model explanation.
    """
    visible_rows = rows[:MAX_MODEL_SQL_ROWS]

    return {
        "rows": visible_rows,
        "returned_to_model": len(visible_rows),
        "total_rows_received": len(rows),
        "truncated": len(rows) > len(visible_rows),
    }
