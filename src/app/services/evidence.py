from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.graphs.state import FinancialState


def build_evidence_bundle(
    state: "FinancialState",
) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "question": state["question"],
    }

    sql_analysis = state.get("sql_analysis")

    if sql_analysis:
        evidence["sql"] = {
            "query": sql_analysis.sql_query,
            "row_count": sql_analysis.row_count,
            "rows": sql_analysis.rows,
        }

    data_analysis = state.get("data_analysis")

    if data_analysis:
        evidence["analytics"] = data_analysis.model_dump(mode="json")
        if data_analysis.chart:
            evidence["chart"] = {
                "filename": data_analysis.chart.filename,
                "chart_type": data_analysis.chart.chart_type,
                "title": data_analysis.chart.title,
                "data_points": data_analysis.chart.data_points,
                "truncated": data_analysis.chart.truncated,
            }


    policy_analysis = state.get("policy_analysis")

    if policy_analysis:
        evidence["policy"] = policy_analysis.model_dump(mode="json")

    risk_analysis = state.get("risk_analysis")

    if risk_analysis:
        evidence["risk"] = risk_analysis.model_dump(mode="json")

    return evidence
