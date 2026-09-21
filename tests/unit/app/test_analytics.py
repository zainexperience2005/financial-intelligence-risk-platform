"""Deterministic calculations retain current numeric and empty-input behavior."""

import pytest

from app.analytics.operations import (
    count_by_category,
    group_and_sum,
    summarize_numeric_column,
)
from app.tools import DataAnalysisInput, DataAnalysisTool


def test_numeric_summary():
    assert summarize_numeric_column([{"v": "2"}, {"v": 4}, {"v": None}], "v") == {
        "count": 2,
        "sum": 6.0,
        "mean": 3.0,
        "min": 2.0,
        "max": 4.0,
    }


def test_empty_summary():
    assert summarize_numeric_column([], "v") == {
        "count": 0,
        "sum": 0.0,
        "mean": None,
        "min": None,
        "max": None,
    }


def test_group_sum_is_sorted_and_does_not_mutate_rows():
    rows = [{"g": "a", "v": "2"}, {"g": "b", "v": "5"}, {"g": "a", "v": "1"}]
    assert group_and_sum(rows, "g", "v") == [{"g": "b", "v": 5}, {"g": "a", "v": 3}]
    assert rows[0]["v"] == "2"


def test_category_counts_include_null():
    result = count_by_category([{"s": "ok"}, {"s": "ok"}, {"s": None}], "s")
    assert sum(row["count"] for row in result) == 3
    assert result[0] == {"s": "ok", "count": 2}


@pytest.mark.parametrize(
    "operation,kwargs",
    [
        ("summarize", {}),
        ("group_sum", {}),
        ("count_by_category", {}),
        ("summarize", {"column": "missing"}),
        ("summarize", {"column": "v", "rows": [{"v": "invalid"}]}),
        ("group_sum", {"group_by": "missing", "value_column": "v"}),
    ],
)
def test_tool_returns_controlled_errors(operation, kwargs):
    args = {"rows": [{"v": 1}], **kwargs}
    result = DataAnalysisTool().execute(DataAnalysisInput(operation=operation, **args))
    assert not result.success
    assert result.error
    assert result.data is None


@pytest.mark.parametrize(
    "operation,kwargs,expected",
    [
        (
            "summarize",
            {"column": "v"},
            {"count": 1, "sum": 2.0, "mean": 2.0, "min": 2.0, "max": 2.0},
        ),
        ("group_sum", {"group_by": "g", "value_column": "v"}, [{"g": "a", "v": 2}]),
        ("count_by_category", {"column": "g"}, [{"g": "a", "count": 1}]),
    ],
)
def test_tool_operations(operation, kwargs, expected):
    result = DataAnalysisTool().execute(
        DataAnalysisInput(operation=operation, rows=[{"g": "a", "v": 2}], **kwargs)
    )
    assert result.success and result.data == expected


def test_empty_group_and_counts():
    assert group_and_sum([], "g", "v") == []
    assert count_by_category([], "g") == []
