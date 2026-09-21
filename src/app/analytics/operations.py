from typing import Any

import pandas as pd


def summarize_numeric_column(
    rows: list[dict[str, Any]],
    column: str,
) -> dict[str, Any]:
    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        return {
            "count": 0,
            "sum": 0.0,
            "mean": None,
            "min": None,
            "max": None,
        }

    if column not in dataframe.columns:
        raise ValueError(
            f"Column not found: {column}"
        )

    numeric = pd.to_numeric(
        dataframe[column],
        errors="raise",
    )

    return {
        "count": int(numeric.count()),
        "sum": float(numeric.sum()),
        "mean": float(numeric.mean()),
        "min": float(numeric.min()),
        "max": float(numeric.max()),
    }


def group_and_sum(
    rows: list[dict[str, Any]],
    group_by: str,
    value_column: str,
) -> list[dict[str, Any]]:
    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        return []

    required = {
        group_by,
        value_column,
    }

    missing = required - set(
        dataframe.columns
    )

    if missing:
        raise ValueError(
            "Missing columns: "
            + ", ".join(sorted(missing))
        )

    dataframe[value_column] = pd.to_numeric(
        dataframe[value_column],
        errors="raise",
    )

    result = (
        dataframe
        .groupby(
            group_by,
            dropna=False,
        )[value_column]
        .sum()
        .reset_index()
        .sort_values(
            value_column,
            ascending=False,
        )
    )

    return result.to_dict(
        orient="records"
    )


def count_by_category(
    rows: list[dict[str, Any]],
    column: str,
) -> list[dict[str, Any]]:
    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        return []

    if column not in dataframe.columns:
        raise ValueError(
            f"Column not found: {column}"
        )

    result = (
        dataframe[column]
        .value_counts(dropna=False)
        .rename_axis(column)
        .reset_index(name="count")
    )

    return result.to_dict(
        orient="records"
    )