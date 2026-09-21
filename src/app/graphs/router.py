"""Deterministic graph routing functions for the Financial Intelligence platform.

Routing Principle:
Routing decisions inspect explicit structured graph state (Pydantic models)
and return typed literals. Normal Python makes the decision reliably without
wasting LLM tokens or introducing non-deterministic routing hallucinations.
"""

from typing import Literal

from app.graphs.state import FinancialState


def route_after_analysis(
    state: FinancialState,
) -> Literal["data_required", "complete"]:
    """Routes after financial analyst assessment to end or request additional data."""
    analysis = state["analysis"]

    if analysis.requires_data:
        return "data_required"

    return "complete"


def route_after_planning(
    state: FinancialState,
) -> Literal["sql", "analyze"]:
    plan = state["plan"]

    if plan.requires_sql:
        return "sql"

    return "analyze"


def route_after_sql(
    state: FinancialState,
) -> Literal[
    "analytics",
    "policy",
    "analyze",
]:
    plan = state["plan"]

    if plan.requires_analytics:
        return "analytics"

    if plan.requires_policy:
        return "policy"

    return "analyze"


def route_after_analytics(
    state: FinancialState,
) -> Literal[
    "policy",
    "analyze",
]:
    if state["plan"].requires_policy:
        return "policy"

    return "analyze"
